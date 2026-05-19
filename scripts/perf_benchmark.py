#!/usr/bin/env python3
"""性能基准测试 —— 对指定问题列表多次评测，生成延迟分布报告。

用法：
    python scripts/perf_benchmark.py --questions 20 --runs 3 --output artifacts/perf/
"""

from __future__ import annotations

import argparse
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

BENCH_QUESTIONS = [
    "浓硫酸稀释的正确操作步骤是什么？",
    "实验室发生火灾时正确的处置流程是什么？",
    "进入化学实验室必须佩戴哪些个人防护装备？",
    "使用乙醚时需要注意哪些安全事项？",
    "可以用湿手插拔电源插头吗？为什么？",
    "使用离心机的安全操作规程是什么？",
    "实验室化学品应该如何分类储存？",
    "氢氟酸为什么特别危险？",
    "生物安全柜和超净工作台有什么区别？",
    "强酸溅到眼睛了应该怎么处理？",
    "使用液氮时需要注意什么安全事项？",
    "实验室气瓶使用的安全要求有哪些？",
    "钠金属应该如何安全储存？",
    "水银温度计打破了应该怎么处理？",
    "实验室突然停电应该怎么处理？",
    "高压灭菌锅的安全操作流程是什么？",
    "使用马弗炉时需要注意哪些安全事项？",
    "实验室有哪些常见的禁止行为？",
    "核磁共振波谱仪使用前需要了解哪些安全知识？",
    "实验室废液应该怎么分类收集？",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Performance benchmark for lab safety assistant")
    p.add_argument("--questions", type=int, default=20, help="Number of questions to use (from built-in list)")
    p.add_argument("--runs", type=int, default=3, help="Runs per question")
    p.add_argument("--output", default="artifacts/perf/", help="Output directory")
    p.add_argument("--api-base", default=DEFAULT_API, help=f"API base URL (default: {DEFAULT_API})")
    p.add_argument("--timeout", type=int, default=120, help="Per-request timeout in seconds")
    p.add_argument("--warmup", type=int, default=3, help="Warmup rounds (results discarded)")
    return p.parse_args()


def run_one(api_base: str, question: str, timeout: int) -> tuple[int, bool]:
    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{api_base.rstrip('/')}/api/chat",
            json={"question": question},
            timeout=(20, timeout),
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        return elapsed_ms, resp.status_code == 200
    except Exception:
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        return elapsed_ms, False


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    questions = BENCH_QUESTIONS[: args.questions]
    all_latencies: list[dict[str, Any]] = []

    # Warmup
    if args.warmup > 0:
        warmup_q = questions[: min(3, len(questions))]
        print(f"Warming up ({args.warmup} rounds, {len(warmup_q)} questions)...")
        for _ in range(args.warmup):
            for q in warmup_q:
                run_one(args.api_base, q, args.timeout)
        print("Warmup done.\n")

    # Benchmark
    total_runs = len(questions) * args.runs
    completed = 0
    all_times: list[int] = []
    failures = 0

    for run_idx in range(args.runs):
        print(f"=== Run {run_idx + 1}/{args.runs} ===")
        for idx, q in enumerate(questions):
            elapsed_ms, ok = run_one(args.api_base, q, args.timeout)
            status = "OK" if ok else "FAIL"
            all_latencies.append({
                "run": run_idx + 1,
                "question_index": idx,
                "question": q[:80],
                "elapsed_ms": elapsed_ms,
                "success": ok,
            })
            if ok:
                all_times.append(elapsed_ms)
            else:
                failures += 1
            completed += 1
            print(f"  [{completed}/{total_runs}] {q[:50]}... {status} {elapsed_ms}ms")

    # Stats
    all_times.sort()
    n = len(all_times)
    print(f"\n=== Results ===")
    print(f"Total runs: {total_runs} | Success: {n} | Failures: {failures}")

    if n == 0:
        print("No successful runs — cannot compute stats.")
        return 1

    def pct(p: float) -> float:
        return float(all_times[min(n - 1, int(n * p / 100))])

    stats = {
        "count": n,
        "avg_ms": round(sum(all_times) / n, 1),
        "min_ms": all_times[0],
        "max_ms": all_times[-1],
        "p50_ms": pct(50),
        "p90_ms": pct(90),
        "p95_ms": pct(95),
        "p99_ms": pct(99),
    }
    for k, v in stats.items():
        print(f"  {k}: {v}")

    target = 3000
    p95_target = 5000
    print(f"\n  -> avg {stats['avg_ms']}ms vs target <{target}ms {'PASS' if stats['avg_ms'] < target else 'FAIL'}")
    print(f"  -> P95 {stats['p95_ms']}ms vs target <{p95_target}ms {'PASS' if stats['p95_ms'] < p95_target else 'FAIL'}")

    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"perf_benchmark_{ts}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"stats": stats, "runs": all_latencies, "config": vars(args)}, f, ensure_ascii=False, indent=2)
    print(f"\nRaw data saved to: {json_path}")

    md_path = out_dir / f"perf_benchmark_{ts}.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# 性能基准测试报告\n\n")
        f.write(f"> 日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"> 题目数：{len(questions)} × {args.runs} 轮 = {total_runs} 次请求\n\n")
        f.write(f"## 延迟分布\n\n")
        f.write(f"| 指标 | 数值 | 目标 | 状态 |\n")
        f.write(f"|------|------|------|------|\n")
        f.write(f"| 平均 | {stats['avg_ms']}ms | <{target}ms | {'✅' if stats['avg_ms'] < target else '❌'} |\n")
        f.write(f"| P50 | {stats['p50_ms']}ms | - | - |\n")
        f.write(f"| P95 | {stats['p95_ms']}ms | <{p95_target}ms | {'✅' if stats['p95_ms'] < p95_target else '❌'} |\n")
        f.write(f"| P99 | {stats['p99_ms']}ms | - | - |\n")
        f.write(f"| 最快 | {stats['min_ms']}ms | - | - |\n")
        f.write(f"| 最慢 | {stats['max_ms']}ms | - | - |\n")
        f.write(f"| 成功率 | {n}/{total_runs} ({round(100*n/total_runs,1)}%) | - | - |\n")
    print(f"Report saved to: {md_path}")

    return 0 if stats["avg_ms"] < target and stats["p95_ms"] < p95_target else 1


if __name__ == "__main__":
    raise SystemExit(main())
