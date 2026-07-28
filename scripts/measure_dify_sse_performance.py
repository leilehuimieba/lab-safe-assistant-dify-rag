#!/usr/bin/env python3
"""Measure Dify Chat API SSE latency without persisting credentials.

The tool records response-header latency, first SSE event latency, first answer
event latency, and complete stream latency.  It reads the App API key only from
an environment variable and never writes the key to an artifact.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests


def percentile(values: Iterable[float], quantile: float) -> float | None:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 1)


def summarize_samples(samples: list[dict]) -> dict[str, int | float | None]:
    successes = [sample for sample in samples if sample.get("success")]

    def metric(name: str) -> list[float]:
        return [
            float(sample[name])
            for sample in successes
            if sample.get(name) is not None
        ]

    summary: dict[str, int | float | None] = {
        "sample_count": len(samples),
        "success_count": len(successes),
        "failure_count": len(samples) - len(successes),
    }
    for name in ("header_ms", "first_event_ms", "first_answer_ms", "total_ms"):
        values = metric(name)
        summary[f"{name.removesuffix('_ms')}_avg_ms"] = (
            round(statistics.fmean(values), 1) if values else None
        )
        summary[f"{name.removesuffix('_ms')}_p50_ms"] = percentile(values, 0.50)
        summary[f"{name.removesuffix('_ms')}_p95_ms"] = percentile(values, 0.95)
        summary[f"{name.removesuffix('_ms')}_max_ms"] = (
            round(max(values), 1) if values else None
        )
    return summary


def evaluate_first_event_target(
    summary: dict[str, int | float | None],
    *,
    target_ms: float,
) -> dict[str, float | bool | None]:
    """Evaluate the acceptance target without hiding failed requests.

    A P95 computed only from successful samples is not sufficient on its own:
    every measured request must also succeed, otherwise a fast subset could make
    an unhealthy run look compliant.
    """
    measured = summary.get("first_event_p95_ms")
    sample_count = int(summary.get("sample_count") or 0)
    success_count = int(summary.get("success_count") or 0)
    failure_count = int(summary.get("failure_count") or 0)
    all_samples_succeeded = (
        sample_count > 0
        and success_count == sample_count
        and failure_count == 0
    )
    passed = bool(
        all_samples_succeeded
        and measured is not None
        and float(measured) <= float(target_ms)
    )
    return {
        "target_ms": float(target_ms),
        "measured_p95_ms": None if measured is None else float(measured),
        "all_samples_succeeded": all_samples_succeeded,
        "passed": passed,
    }


def read_questions(path: Path, limit: int) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return []
    candidate_columns = ("question", "问题", "query")
    column = next((name for name in candidate_columns if name in rows[0]), None)
    if column is None:
        raise ValueError(
            f"Question column not found; expected one of {candidate_columns}, "
            f"got {tuple(rows[0])}"
        )
    questions = [
        str(row.get(column, "")).strip()
        for row in rows
        if str(row.get(column, "")).strip()
    ]
    return questions[:limit] if limit > 0 else questions


def measure_one(
    *,
    base_url: str,
    api_key: str,
    question: str,
    timeout: float,
    user_prefix: str,
) -> dict:
    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/v1"):
        endpoint += "/v1"
    endpoint += "/chat-messages"
    payload = {
        "inputs": {},
        "query": question,
        "response_mode": "streaming",
        "user": f"{user_prefix}-{uuid.uuid4().hex[:12]}",
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    started = time.perf_counter()
    sample = {
        "question": question,
        "success": False,
        "http_status": None,
        "header_ms": None,
        "first_event_ms": None,
        "first_answer_ms": None,
        "total_ms": None,
        "event_count": 0,
        "finish_event": "",
        "error": "",
    }
    response = None
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=(12, timeout),
        )
        sample["http_status"] = response.status_code
        sample["header_ms"] = round((time.perf_counter() - started) * 1000, 1)
        response.raise_for_status()
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data:"):
                continue
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            if sample["first_event_ms"] is None:
                sample["first_event_ms"] = elapsed_ms
            sample["event_count"] += 1
            body = raw_line[5:].strip()
            try:
                event = json.loads(body)
            except json.JSONDecodeError:
                continue
            event_name = str(event.get("event", ""))
            if (
                sample["first_answer_ms"] is None
                and event_name in {"message", "agent_message", "text_chunk"}
            ):
                sample["first_answer_ms"] = elapsed_ms
            if event_name in {
                "message_end",
                "workflow_finished",
                "agent_message_end",
                "error",
            }:
                sample["finish_event"] = event_name
        sample["total_ms"] = round((time.perf_counter() - started) * 1000, 1)
        sample["success"] = (
            response.status_code == 200
            and sample["first_event_ms"] is not None
            and sample["finish_event"] not in {"error", ""}
        )
        if sample["first_answer_ms"] is None:
            sample["first_answer_ms"] = sample["first_event_ms"]
    except Exception as exc:
        sample["total_ms"] = round((time.perf_counter() - started) * 1000, 1)
        sample["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if response is not None:
            response.close()
    return sample


def write_outputs(
    samples: list[dict],
    *,
    output_csv: Path,
    report_md: Path,
    base_url: str,
    warmup_count: int = 0,
    first_event_target_ms: float | None = None,
) -> dict:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(samples[0]) if samples else [
        "question",
        "success",
        "http_status",
        "header_ms",
        "first_event_ms",
        "first_answer_ms",
        "total_ms",
        "event_count",
        "finish_event",
        "error",
    ]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)

    summary = summarize_samples(samples)
    target_result = (
        evaluate_first_event_target(summary, target_ms=first_event_target_ms)
        if first_event_target_ms is not None
        else None
    )
    if target_result:
        summary["warmup_count"] = warmup_count
        summary["first_event_target_ms"] = target_result["target_ms"]
        summary["first_event_target_passed"] = target_result["passed"]
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [
        "# Dify SSE 性能实测",
        "",
        f"> 生成时间：{generated_at}",
        f"> Dify 地址：`{base_url}`",
        "> 口径：header=HTTP 响应头；first_event=首个 SSE data 事件；"
        "first_answer=首个回答事件；total=完整流结束。",
        "> App Key 仅从环境变量读取，未写入报告或 CSV。",
        "",
        "## 汇总",
        "",
        f"- 样本：{summary['sample_count']}",
        f"- 成功：{summary['success_count']}",
        f"- 失败：{summary['failure_count']}",
        f"- 预热请求（不计入样本）：{warmup_count}",
        "",
        "| 指标 | 平均 | P50 | P95 | 最大 |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, key in (
        ("HTTP 响应头", "header"),
        ("首个 SSE 事件", "first_event"),
        ("首个回答事件", "first_answer"),
        ("完整流", "total"),
    ):
        values = [
            summary.get(f"{key}_avg_ms"),
            summary.get(f"{key}_p50_ms"),
            summary.get(f"{key}_p95_ms"),
            summary.get(f"{key}_max_ms"),
        ]
        rendered = ["—" if value is None else f"{value:.1f} ms" for value in values]
        lines.append(f"| {label} | {' | '.join(rendered)} |")
    if target_result:
        result_text = "通过" if target_result["passed"] else "未通过"
        measured_text = (
            "—"
            if target_result["measured_p95_ms"] is None
            else f"{target_result['measured_p95_ms']:.1f} ms"
        )
        lines.extend(
            [
                "",
                "## 验收判定",
                "",
                f"- 首个 SSE 事件 P95 目标：≤ {target_result['target_ms']:.1f} ms",
                f"- 实测：{measured_text}",
                f"- 全部正式样本成功：{'是' if target_result['all_samples_succeeded'] else '否'}",
                f"- 判定：**{result_text}**",
            ]
        )
    lines.extend(
        [
            "",
            "## 结论边界",
            "",
            "- 首事件/首字节与完整回答耗时是不同指标，不得互相替代。",
            "- 样本量较小时只作为阶段证据；正式结项应保留原始 CSV 并继续扩样。",
            "- 完整回答耗时受模型、网络、工作流和输出长度共同影响。",
            "",
            f"原始数据：`{output_csv.as_posix()}`",
        ]
    )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key-env", default="DIFY_APP_API_KEY")
    parser.add_argument("--questions-csv", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Warm-up requests excluded from the formal sample set (default: 1).",
    )
    parser.add_argument(
        "--max-first-event-p95-ms",
        type=float,
        default=3000.0,
        help="Fail the run unless all samples succeed and first-event P95 is within this limit.",
    )
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--user-prefix", default="labsafe-sse-perf")
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--report-md", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    api_key = os.getenv(args.api_key_env, "").strip()
    if not api_key:
        raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")
    questions = read_questions(args.questions_csv, args.limit)
    if not questions:
        raise SystemExit("No questions found")
    warmup_count = max(0, args.warmup)
    for index in range(warmup_count):
        print(f"[warmup {index + 1}/{warmup_count}] {questions[0][:60]}", flush=True)
        warmup_sample = measure_one(
            base_url=args.base_url,
            api_key=api_key,
            question=questions[0],
            timeout=args.timeout,
            user_prefix=f"{args.user_prefix}-warmup",
        )
        print(
            "  "
            f"success={warmup_sample['success']} "
            f"first_event_ms={warmup_sample['first_event_ms']} "
            f"error={warmup_sample['error']}",
            flush=True,
        )

    samples = []
    for index, question in enumerate(questions, 1):
        print(f"[{index}/{len(questions)}] {question[:60]}", flush=True)
        sample = measure_one(
            base_url=args.base_url,
            api_key=api_key,
            question=question,
            timeout=args.timeout,
            user_prefix=args.user_prefix,
        )
        samples.append(sample)
        print(
            "  "
            f"success={sample['success']} first_event_ms={sample['first_event_ms']} "
            f"total_ms={sample['total_ms']} error={sample['error']}",
            flush=True,
        )
    summary = write_outputs(
        samples,
        output_csv=args.output_csv,
        report_md=args.report_md,
        base_url=args.base_url,
        warmup_count=warmup_count,
        first_event_target_ms=args.max_first_event_p95_ms,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("first_event_target_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
