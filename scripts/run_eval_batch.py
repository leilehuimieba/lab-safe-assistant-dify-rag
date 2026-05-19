#!/usr/bin/env python3
"""批量评测脚本 —— 对评测集中的问题逐条调用 API，生成原始评测结果供人工打分。

用法（本地服务已启动）：
    python scripts/run_eval_batch.py --eval-set eval_set_v2_50.csv --output artifacts/eval_50/

输出：
    - eval_50_raw.json     原始评测结果（JSON 数组）
    - eval_50_for_review.csv  供人工评分的 CSV（含 answer + citations）
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch eval runner for lab safety assistant")
    p.add_argument("--eval-set", required=True, help="Path to eval set CSV")
    p.add_argument("--output", required=True, help="Output directory for results")
    p.add_argument("--api-base", default=DEFAULT_API, help=f"API base URL (default: {DEFAULT_API})")
    p.add_argument("--timeout", type=int, default=120, help="Per-request timeout in seconds")
    return p.parse_args()


def run_one(api_base: str, question: str, timeout: int) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{api_base.rstrip('/')}/api/chat",
            json={"question": question},
            timeout=(20, timeout),
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        if resp.status_code == 200:
            body = resp.json()
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
                "citations": body.get("citations", []),
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
                "citations": [],
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
            "citations": [],
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
    for idx, row in enumerate(eval_rows, 1):
        qid = row.get("id", f"Q{idx}")
        question = row.get("question", "").strip()
        category = row.get("category", "")
        subcategory = row.get("subcategory", "")

        if not question:
            print(f"  [{idx}/{len(eval_rows)}] {qid}: SKIP (empty question)")
            continue

        print(f"  [{idx}/{len(eval_rows)}] {qid}: {question[:60]}...", end=" ", flush=True)
        result = run_one(args.api_base, question, args.timeout)
        status = "OK" if result["http_status"] == 200 else f"ERR {result['http_status']}"
        print(f"{status} {result['elapsed_ms']}ms {result['decision']}")

        results.append({
            "eval_id": qid,
            "category": category,
            "subcategory": subcategory,
            "expected_answer_type": row.get("expected_answer_type", ""),
            "expected_keywords": row.get("expected_keywords", ""),
            "question": question,
            **result,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })

    # --- Save raw JSON ---
    json_path = out_dir / "eval_50_raw.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nRaw results saved to: {json_path}")

    # --- Save review CSV ---
    csv_path = out_dir / "eval_50_for_review.csv"
    review_headers = [
        "eval_id", "category", "subcategory", "question",
        "answer", "decision", "model", "elapsed_ms", "low_confidence",
        "http_status", "error",
        "citation_0_title", "citation_0_snippet",
        "citation_1_title", "citation_1_snippet",
        "citation_2_title", "citation_2_snippet",
        "expected_answer_type", "expected_keywords",
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
    for r in results:
        d = r.get("decision", "unknown")
        decisions[d] = decisions.get(d, 0) + 1

    print(f"\n=== Summary ===")
    print(f"Total: {len(results)} | Success: {success}/{len(results)}")
    if times:
        times.sort()
        print(f"Response time - avg: {round(sum(times)/len(times))}ms | median: {times[len(times)//2]}ms | max: {max(times)}ms")
    print(f"Decisions: {decisions}")

    # Generate summary markdown
    md_path = out_dir / "eval_50_summary.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# 50 题评测报告\n\n")
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
        f.write(f"## 人工评分\n\n")
        f.write(f"待人工评分后填写。评分标准：\n")
        f.write(f"- 3 分（完全正确）：回答准确、引用可靠、步骤完整\n")
        f.write(f"- 2 分（基本可用）：回答方向正确，但不够完整或存在轻微冗余\n")
        f.write(f"- 1 分（不可用）：回答错误、遗漏关键安全信息或存在安全隐患\n\n")
        f.write(f"人工评分 CSV：`eval_50_for_review.csv`\n")

    print(f"Summary saved to: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
