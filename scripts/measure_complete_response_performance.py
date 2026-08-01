#!/usr/bin/env python3
"""Measure complete HTTP response latency for the deployed `/api/chat` endpoint.

Unlike the Dify SSE probe, this script measures from sending an HTTP request
until the complete JSON answer has been received.  It is deliberately strict:
all formal requests must return HTTP 200 and a final non-empty answer, and the
complete-response P95 must be *strictly* below the configured target.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


TERMINAL_DECISIONS = {
    "rule_blocked",
    "need_more_info",
    "emergency_redirect",
    "rule_direct_answer",
}


def load_demo_password(repo_root: Path) -> str:
    configured = os.getenv("DEMO_PASSWORD", "").strip()
    if configured:
        return configured
    env_file = repo_root / ".env.web_demo"
    if not env_file.is_file():
        return ""
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and key.strip() == "DEMO_PASSWORD":
            return value.strip().strip('"').strip("'")
    return ""


def is_complete_final_answer(answer: str, decision: str) -> bool:
    """Accept a fully returned final answer without misclassifying rule replies.

    A terminal safety rule may correctly refuse or request missing context, so it
    must not be forced into the ordinary conclusion/steps/forbidden template.
    """

    text = (answer or "").strip()
    if not text:
        return False
    if (decision or "").strip() in TERMINAL_DECISIONS:
        return True
    return "结论:" in text and "禁止事项:" in text and (
        "步骤:" in text or "立即处理:" in text
    )


def percentile95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * 0.95) - 1]


def evaluate_complete_response_target(samples: list[dict[str, Any]], *, target_ms: float) -> dict[str, Any]:
    successful = [item for item in samples if int(item.get("http_status") or 0) == 200]
    values = [float(item["elapsed_ms"]) for item in successful if item.get("elapsed_ms") is not None]
    p95 = percentile95(values)
    answer_count = sum(bool(item.get("answer_nonempty")) for item in samples)
    return {
        "sample_count": len(samples),
        "success_count": len(successful),
        "nonempty_final_answer_count": answer_count,
        "p50_ms": sorted(values)[len(values) // 2] if values else None,
        "p95_ms": p95,
        "max_ms": max(values) if values else None,
        "avg_ms": round(statistics.mean(values), 1) if values else None,
        "target_ms": target_ms,
        "passed": (
            len(successful) == len(samples)
            and answer_count == len(samples)
            and p95 is not None
            and p95 < target_ms
        ),
    }


def load_questions(path: Path, limit: int) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    column = next((name for name in ("question", "问题", "query") if rows and name in rows[0]), None)
    if column is None:
        raise ValueError("Question column not found; expected question, 问题, or query")
    questions = [str(row.get(column) or "").strip() for row in rows]
    questions = [item for item in questions if item]
    return questions[:limit] if limit > 0 else questions


def measure_one(*, api_base: str, demo_password: str, question: str, timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    question_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()
    try:
        response = requests.post(
            f"{api_base.rstrip('/')}/api/chat",
            json={"mode": "lab", "question": question},
            headers={"x-password": demo_password},
            timeout=(5, timeout),
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        body = response.json() if "application/json" in response.headers.get("Content-Type", "").lower() else {}
        answer = str(body.get("answer") or "")
        decision = str(body.get("decision") or "")
        return {
            "question_sha256": question_hash,
            "http_status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "server_elapsed_ms": body.get("elapsed_ms"),
            "model": body.get("model", ""),
            "decision": decision,
            "answer_nonempty": is_complete_final_answer(answer, decision),
            "upstream_ms": (body.get("timings") or {}).get("upstream_ms"),
            "error": "" if response.status_code == 200 else str(body)[:200],
        }
    except Exception as exc:
        return {
            "question_sha256": question_hash,
            "http_status": 0,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
            "server_elapsed_ms": None,
            "model": "",
            "decision": "",
            "answer_nonempty": False,
            "upstream_ms": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", required=True)
    parser.add_argument("--questions-csv", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--target-ms", type=float, default=3000.0)
    parser.add_argument("--demo-password", default="", help=argparse.SUPPRESS)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--report-md", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    password = args.demo_password or load_demo_password(repo_root)
    if not password:
        raise SystemExit("Missing DEMO_PASSWORD (environment, .env.web_demo, or --demo-password)")
    questions = load_questions(args.questions_csv, args.limit)
    if not questions:
        raise SystemExit("No questions found")

    for index in range(max(0, args.warmup)):
        sample = measure_one(api_base=args.api_base, demo_password=password, question=questions[0], timeout=args.timeout)
        print(f"[warmup {index + 1}/{args.warmup}] status={sample['http_status']} elapsed_ms={sample['elapsed_ms']}", flush=True)

    samples: list[dict[str, Any]] = []
    for index, question in enumerate(questions, 1):
        sample = measure_one(api_base=args.api_base, demo_password=password, question=question, timeout=args.timeout)
        samples.append(sample)
        print(f"[{index}/{len(questions)}] status={sample['http_status']} elapsed_ms={sample['elapsed_ms']} model={sample['model']}", flush=True)

    summary = evaluate_complete_response_target(samples, target_ms=args.target_ms)
    summary["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    summary["measurement"] = "HTTP request sent to complete JSON answer received; warmups excluded"
    summary["model_counts"] = dict(Counter(str(item.get("model") or "") for item in samples))

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(samples[0]) if samples else [])
        writer.writeheader()
        writer.writerows(samples)
    result = "通过" if summary["passed"] else "未通过"
    args.report_md.write_text(
        "\n".join(
            [
                "# 用户端完整回答性能实测",
                "",
                "> 口径：从发送 `/api/chat` HTTP 请求到收到完整 JSON `answer`；不是 Dify SSE 首事件。",
                "> 终端安全规则可正确地直接拒绝或要求补充信息，不强行套用常规模板。",
                "",
                "## 汇总",
                "",
                f"- 样本：{summary['sample_count']}；HTTP 200：{summary['success_count']}；完整最终回答：{summary['nonempty_final_answer_count']}",
                f"- 平均：{summary['avg_ms']} ms；P50：{summary['p50_ms']} ms；P95：{summary['p95_ms']} ms；最大：{summary['max_ms']} ms",
                f"- 目标：完整回答 P95 < {summary['target_ms']:.1f} ms；判定：**{result}**",
                f"- 路由分布：`{json.dumps(summary['model_counts'], ensure_ascii=False)}`",
                "",
                f"原始数据：`{args.output_csv.as_posix()}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
