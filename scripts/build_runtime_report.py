#!/usr/bin/env python3
"""基于 health_snapshots.csv 生成周报 / 月报骨架。"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build runtime summary report")
    parser.add_argument(
        "--snapshot-csv",
        default=str(REPO_ROOT / "artifacts" / "runtime" / "health_snapshots.csv"),
        help="Path to runtime snapshot CSV",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "artifacts" / "runtime" / "reports"),
        help="Directory for generated runtime reports",
    )
    parser.add_argument(
        "--label",
        default="latest",
        help="Report label, e.g. week1 / 2026W21 / month1 / latest",
    )
    return parser.parse_args()


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> int:
    args = parse_args()
    snapshot_csv = Path(args.snapshot_csv).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not snapshot_csv.exists():
        raise SystemExit(f"Missing snapshot csv: {snapshot_csv}")

    with snapshot_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit("No snapshot rows found")

    ok_rows = [row for row in rows if str(row.get("health_ok", "")).lower() == "true"]
    dify_rows = [row for row in rows if str(row.get("dify_reachable", "")).lower() == "true"]
    avg_ms_values = [v for row in rows if (v := parse_float(row.get("recent_avg_ms", ""))) is not None]
    p95_values = [v for row in rows if (v := parse_float(row.get("recent_p95_ms", ""))) is not None]
    max_values = [v for row in rows if (v := parse_float(row.get("recent_max_ms", ""))) is not None]

    last = rows[-1]
    report_md = out_dir / f"runtime_{args.label}_summary.md"
    report_csv = out_dir / f"runtime_{args.label}_summary.csv"

    with report_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "generated_at",
                "label",
                "sample_count",
                "health_ok_rate",
                "dify_reachable_rate",
                "avg_recent_ms",
                "avg_recent_p95_ms",
                "max_recent_ms",
                "last_kb_rows",
                "last_kb_imported",
                "last_runtime_started_at",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "label": args.label,
                "sample_count": len(rows),
                "health_ok_rate": round(len(ok_rows) / len(rows) * 100, 1),
                "dify_reachable_rate": round(len(dify_rows) / len(rows) * 100, 1),
                "avg_recent_ms": round(avg(avg_ms_values), 1),
                "avg_recent_p95_ms": round(avg(p95_values), 1),
                "max_recent_ms": round(max(max_values), 1) if max_values else 0.0,
                "last_kb_rows": last.get("knowledge_base_rows", ""),
                "last_kb_imported": last.get("knowledge_base_imported", ""),
                "last_runtime_started_at": last.get("runtime_started_at", ""),
            }
        )

    lines = [
        f"# 试运行监测摘要（{args.label}）",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 快照来源：`{snapshot_csv}`",
        "",
        "## 1. 样本统计",
        "",
        f"- 快照数：`{len(rows)}`",
        f"- `/health` 正常率：`{round(len(ok_rows) / len(rows) * 100, 1)}%`",
        f"- Dify 可达率：`{round(len(dify_rows) / len(rows) * 100, 1)}%`",
        "",
        "## 2. 性能统计",
        "",
        f"- recent_avg_ms 均值：`{round(avg(avg_ms_values), 1)}`",
        f"- recent_p95_ms 均值：`{round(avg(p95_values), 1)}`",
        f"- recent_max_ms 最大值：`{round(max(max_values), 1) if max_values else 0.0}`",
        "",
        "## 3. 最近一次快照",
        "",
        f"- captured_at：`{last.get('captured_at', '')}`",
        f"- knowledge_base_rows：`{last.get('knowledge_base_rows', '')}`",
        f"- knowledge_base_imported：`{last.get('knowledge_base_imported', '')}`",
        f"- runtime_started_at：`{last.get('runtime_started_at', '')}`",
        "",
        "## 4. 本期问题与动作（待人工填写）",
        "",
        "- 主要问题：",
        "- 处理动作：",
        "- 下周计划：",
        "",
        "## 5. 说明",
        "",
        "- 这份报告是 7×24 / 3个月试运行的证据骨架；",
        "- 当快照样本积累到按天/按周稳定采集后，可直接作为周报/月报基础材料。",
        "",
    ]
    report_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] runtime report md: {report_md}")
    print(f"[OK] runtime report csv: {report_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
