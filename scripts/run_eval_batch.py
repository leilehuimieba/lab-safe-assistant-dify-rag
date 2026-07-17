#!/usr/bin/env python3
"""批量评测脚本 —— 对评测集中的问题逐条调用 API，生成原始评测结果供人工打分。

用法（本地服务已启动）：
    python scripts/run_eval_batch.py --eval-set eval_set_v2_50.csv --output artifacts/eval_50/

输出：
    - <eval_set_stem>_raw.json         原始评测结果（JSON 数组）
    - <eval_set_stem>_for_review.csv   供人工评分的 CSV（含 answer + citations）

特性：
    - 自动兼容旧版评测集 `eval_set_v1.csv`
    - 支持新版“申报书对齐回归集”字段
    - 支持按 `conversation_group` 复用 `session_id` 进行多轮评测
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_API = os.getenv("EVAL_API_BASE", "http://127.0.0.1:8088")


def load_demo_password() -> str:
    configured = os.getenv("DEMO_PASSWORD", "").strip()
    if configured:
        return configured
    env_file = REPO_ROOT / ".env.web_demo"
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and key.strip() == "DEMO_PASSWORD":
            return value.strip().strip('"')
    return ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch eval runner for lab safety assistant")
    p.add_argument("--eval-set", required=True, help="Path to eval set CSV")
    p.add_argument("--output", required=True, help="Output directory for results")
    p.add_argument("--api-base", default=DEFAULT_API, help=f"API base URL (default: {DEFAULT_API})")
    p.add_argument("--timeout", type=int, default=120, help="Per-request timeout in seconds")
    p.add_argument("--demo-password", default=load_demo_password(), help=argparse.SUPPRESS)
    return p.parse_args()


def run_one(
    api_base: str,
    question: str,
    timeout: int,
    session_id: str = "",
    demo_password: str = "",
) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{api_base.rstrip('/')}/api/chat",
            json={"mode": "lab", "question": question, "session_id": session_id},
            headers={"x-password": demo_password} if demo_password else {},
            timeout=(20, timeout),
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        if resp.status_code == 200:
            body = resp.json()
            timings = body.get("timings", {}) or {}
            return {
                "http_status": resp.status_code,
                "elapsed_ms": elapsed_ms,
                "server_elapsed_ms": body.get("elapsed_ms", 0),
                "session_id": body.get("session_id", ""),
                "answer": body.get("answer", ""),
                "decision": body.get("decision", ""),
                "model": body.get("model", ""),
                "risk_level": body.get("risk_level", ""),
                "matched_rule_id": body.get("matched_rule_id", ""),
                "matched_rule_action": body.get("matched_rule_action", ""),
                "low_confidence": body.get("low_confidence", False),
                "low_confidence_reason": body.get("low_confidence_reason", ""),
                "answer_possibly_truncated": body.get("answer_possibly_truncated", False),
                "citations": body.get("citations", []),
                "cache_hit": bool(timings.get("cache_hit", False)),
                "retrieve_ms": timings.get("retrieve_ms", 0),
                "rule_ms": timings.get("rule_ms", 0),
                "cache_lookup_ms": timings.get("cache_lookup_ms", 0),
                "upstream_ms": timings.get("upstream_ms", 0),
                "error": "",
            }
        else:
            return {
                "http_status": resp.status_code,
                "elapsed_ms": elapsed_ms,
                "answer": "",
                "decision": "",
                "model": "",
                "risk_level": "",
                "matched_rule_id": "",
                "matched_rule_action": "",
                "low_confidence": False,
                "low_confidence_reason": "",
                "answer_possibly_truncated": False,
                "citations": [],
                "cache_hit": False,
                "retrieve_ms": 0,
                "rule_ms": 0,
                "cache_lookup_ms": 0,
                "upstream_ms": 0,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        return {
            "http_status": 0,
            "elapsed_ms": elapsed_ms,
            "answer": "",
            "decision": "",
            "model": "",
            "risk_level": "",
            "matched_rule_id": "",
            "matched_rule_action": "",
            "low_confidence": False,
            "low_confidence_reason": "",
            "answer_possibly_truncated": False,
            "citations": [],
            "cache_hit": False,
            "retrieve_ms": 0,
            "rule_ms": 0,
            "cache_lookup_ms": 0,
            "upstream_ms": 0,
            "error": str(exc),
        }


def main() -> int:
    args = parse_args()

    eval_path = Path(args.eval_set).resolve()
    if not eval_path.exists():
        print(f"ERROR: eval set not found: {eval_path}")
        return 1

    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Read eval questions
    with eval_path.open("r", encoding="utf-8-sig", newline="") as f:
        eval_rows = list(csv.DictReader(f))
    print(f"Loaded {len(eval_rows)} eval questions from {eval_path}")

    results: list[dict[str, Any]] = []
    group_sessions: dict[str, str] = {}
    for idx, row in enumerate(eval_rows, 1):
        qid = row.get("id", f"Q{idx}")
        question = row.get("question", "").strip()
        category = row.get("category", "")
        subcategory = row.get("subcategory", "")
        conversation_group = (row.get("conversation_group", "") or "").strip()
        turn_no = (row.get("turn_no", "") or "").strip()
        reused_session_id = group_sessions.get(conversation_group, "") if conversation_group else ""

        if not question:
            print(f"  [{idx}/{len(eval_rows)}] {qid}: SKIP (empty question)")
            continue

        extra = f" group={conversation_group} turn={turn_no}" if conversation_group else ""
        print(f"  [{idx}/{len(eval_rows)}] {qid}:{extra} {question[:60]}...", end=" ", flush=True)
        result = run_one(
            args.api_base,
            question,
            args.timeout,
            reused_session_id,
            args.demo_password,
        )
        status = "OK" if result["http_status"] == 200 else f"ERR {result['http_status']}"
        print(f"{status} {result['elapsed_ms']}ms {result['decision']} {result['model']}")

        if conversation_group and result.get("session_id"):
            group_sessions[conversation_group] = str(result["session_id"])

        results.append({
            "eval_id": qid,
            "category": category,
            "subcategory": subcategory,
            "risk_level_expected": row.get("risk_level", ""),
            "expected_answer_type": row.get("expected_answer_type", ""),
            "expected_keywords": row.get("expected_keywords", ""),
            "expected_action": row.get("expected_action", ""),
            "expected_lane": row.get("expected_lane", ""),
            "allowed_sources": row.get("allowed_sources", ""),
            "should_refuse": row.get("should_refuse", ""),
            "should_use_fast_path": row.get("should_use_fast_path", ""),
            "should_use_cache": row.get("should_use_cache", ""),
            "should_request_more_info": row.get("should_request_more_info", ""),
            "conversation_group": conversation_group,
            "turn_no": turn_no,
            "prior_context": row.get("prior_context", ""),
            "question": question,
            "input_session_id": reused_session_id,
            **result,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })

    # --- Save raw JSON ---
    stem = eval_path.stem
    json_path = out_dir / f"{stem}_raw.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nRaw results saved to: {json_path}")

    # --- Save review CSV ---
    csv_path = out_dir / f"{stem}_for_review.csv"
    review_headers = [
        "eval_id", "category", "subcategory", "question",
        "conversation_group", "turn_no", "prior_context", "input_session_id", "session_id",
        "answer", "decision", "model", "elapsed_ms", "server_elapsed_ms", "cache_hit",
        "retrieve_ms", "rule_ms", "cache_lookup_ms", "upstream_ms", "low_confidence", "low_confidence_reason",
        "answer_possibly_truncated",
        "http_status", "error",
        "citation_0_title", "citation_0_snippet",
        "citation_1_title", "citation_1_snippet",
        "citation_2_title", "citation_2_snippet",
        "expected_answer_type", "expected_keywords", "expected_action", "expected_lane",
        "allowed_sources", "should_refuse", "should_use_fast_path", "should_use_cache", "should_request_more_info",
        "human_score", "human_notes",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=review_headers, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            row_out = dict(r)
            citations = r.get("citations", []) or []
            for ci in range(3):
                if ci < len(citations):
                    row_out[f"citation_{ci}_title"] = citations[ci].get("title", "")
                    row_out[f"citation_{ci}_snippet"] = (citations[ci].get("snippet", "") or "")[:200]
                else:
                    row_out[f"citation_{ci}_title"] = ""
                    row_out[f"citation_{ci}_snippet"] = ""
            row_out.pop("citations", None)
            row_out["human_score"] = ""
            row_out["human_notes"] = ""
            writer.writerow(row_out)
    print(f"Review CSV saved to: {csv_path}")

    # --- Summary stats ---
    success = sum(1 for r in results if r["http_status"] == 200)
    times = [r["elapsed_ms"] for r in results if r["http_status"] == 200]
    decisions: dict[str, int] = {}
    models: dict[str, int] = {}
    categories: dict[str, int] = {}
    cache_hits = sum(1 for r in results if r.get("cache_hit"))
    for r in results:
        d = r.get("decision", "unknown")
        decisions[d] = decisions.get(d, 0) + 1
        m = r.get("model", "unknown")
        models[m] = models.get(m, 0) + 1
        c = r.get("category", "unknown")
        categories[c] = categories.get(c, 0) + 1

    print(f"\n=== Summary ===")
    print(f"Total: {len(results)} | Success: {success}/{len(results)}")
    if times:
        times.sort()
        print(f"Response time - avg: {round(sum(times)/len(times))}ms | median: {times[len(times)//2]}ms | max: {max(times)}ms")
    print(f"Decisions: {decisions}")
    print(f"Models: {models}")
    print(f"Cache hits: {cache_hits}/{len(results)}")

    # Generate summary markdown
    md_path = out_dir / f"{stem}_summary.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# 批量评测报告：{stem}\n\n")
        f.write(f"> 日期：{datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"> 项目：基于 Dify 的实验室安全小助手\n\n")
        f.write(f"## 总体结果\n\n")
        f.write(f"- 评测题数：{len(results)}\n")
        f.write(f"- HTTP 成功：{success}/{len(results)}\n")
        if times:
            f.write(f"- 平均耗时：{round(sum(times)/len(times))}ms\n")
            f.write(f"- 中位数耗时：{times[len(times)//2]}ms\n")
            f.write(f"- 最大耗时：{max(times)}ms\n")
        f.write(f"- 决策分布：{decisions}\n\n")
        f.write(f"- 模型分布：{models}\n")
        f.write(f"- 缓存命中：{cache_hits}/{len(results)}\n\n")
        f.write(f"## 类别分布\n\n")
        for key, value in sorted(categories.items()):
            f.write(f"- {key}: {value}\n")
        f.write("\n")
        f.write(f"## 人工评分\n\n")
        f.write(f"待人工评分后填写。评分标准：\n")
        f.write(f"- 3 分（完全正确）：回答准确、引用可靠、步骤完整\n")
        f.write(f"- 2 分（基本可用）：回答方向正确，但不够完整或存在轻微冗余\n")
        f.write(f"- 1 分（不可用）：回答错误、遗漏关键安全信息或存在安全隐患\n\n")
        f.write(f"人工评分 CSV：`{stem}_for_review.csv`\n")

    print(f"Summary saved to: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
