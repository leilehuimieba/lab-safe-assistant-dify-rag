#!/usr/bin/env python3
"""基于 health_snapshots.csv 为每个自然日生成阶段证据快照报告，并生成完整日期索引。

- 只统计已有真实快照的日期，不为空缺日期编造数据。
- 空缺日期仍会在索引表中逐日列出，明确标注“无快照”，不悄悄跳过。
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build per-day runtime evidence reports")
    parser.add_argument(
        "--snapshot-csv",
        default=str(REPO_ROOT / "artifacts" / "runtime" / "health_snapshots.csv"),
    )
    parser.add_argument(
        "--daily-output-dir",
        default=str(REPO_ROOT / "artifacts" / "runtime" / "reports" / "daily"),
    )
    parser.add_argument(
        "--index-csv",
        default=str(REPO_ROOT / "artifacts" / "runtime" / "reports" / "daily_index.csv"),
    )
    parser.add_argument(
        "--start-date",
        default="2026-05-22",
        help="Inclusive start of the full calendar-day ledger (monitoring start date)",
    )
    parser.add_argument(
        "--end-date",
        default="",
        help="Inclusive end of the full calendar-day ledger; defaults to the last snapshot's date",
    )
    return parser.parse_args()


def load_rows(snapshot_csv: Path) -> list[dict[str, str]]:
    with snapshot_csv.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def group_by_day(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_day: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        captured_at = (row.get("captured_at") or "").strip()
        if not captured_at:
            continue
        day = captured_at[:10]
        by_day.setdefault(day, []).append(row)
    return by_day


def status_signature(row: dict[str, str]) -> str:
    health_status = (row.get("health_status") or "").strip()
    health_error = (row.get("health_error") or "").strip()
    if row.get("health_ok") == "True":
        return "200(ok)"
    if health_error:
        return "conn-fail"
    return health_status or "unknown"


def write_daily_report(day: str, rows: list[dict[str, str]], out_dir: Path) -> Path:
    ok_rows = [r for r in rows if r.get("health_ok") == "True"]
    dify_rows = [r for r in rows if r.get("dify_reachable") == "True"]
    signatures = sorted({status_signature(r) for r in rows})
    rows_sorted = sorted(rows, key=lambda r: r.get("captured_at", ""))
    first, last = rows_sorted[0], rows_sorted[-1]

    lines = [
        f"# 7x24 试运行 - 单日阶段证据（{day}）",
        "",
        f"> 数据来源：`artifacts/runtime/health_snapshots.csv`（当日 {len(rows)} 条真实快照）",
        "",
        "## 样本统计",
        "",
        f"- 快照数：`{len(rows)}`",
        f"- `/health` 正常率：`{round(len(ok_rows) / len(rows) * 100, 1)}%`",
        f"- Dify 可达率：`{round(len(dify_rows) / len(rows) * 100, 1)}%`",
        f"- 出现的状态类型：`{', '.join(signatures)}`",
        "",
        "## 首末快照",
        "",
        f"- 当日首条：`{first.get('captured_at', '')}`，health_status=`{first.get('health_status', '')}`，health_ok=`{first.get('health_ok', '')}`",
        f"- 当日末条：`{last.get('captured_at', '')}`，health_status=`{last.get('health_status', '')}`，health_ok=`{last.get('health_ok', '')}`",
        "",
        "## 明细",
        "",
        "| captured_at | health_status | health_ok | dify_reachable | knowledge_base_rows |",
        "|---|---|---|---|---|",
    ]
    for r in rows_sorted:
        lines.append(
            f"| {r.get('captured_at', '')} | {r.get('health_status', '')} | {r.get('health_ok', '')} "
            f"| {r.get('dify_reachable', '')} | {r.get('knowledge_base_rows', '')} |"
        )
    lines.append("")

    out_path = out_dir / f"{day}_summary.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def main() -> int:
    args = parse_args()
    snapshot_csv = Path(args.snapshot_csv).resolve()
    daily_dir = Path(args.daily_output_dir).resolve()
    index_csv = Path(args.index_csv).resolve()
    daily_dir.mkdir(parents=True, exist_ok=True)

    if not snapshot_csv.exists():
        raise SystemExit(f"Missing snapshot csv: {snapshot_csv}")

    rows = load_rows(snapshot_csv)
    if not rows:
        raise SystemExit("No snapshot rows found")

    by_day = group_by_day(rows)

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    else:
        end_date = max(datetime.strptime(d, "%Y-%m-%d").date() for d in by_day)

    generated: list[Path] = []
    index_rows = []
    for day in daterange(start_date, end_date):
        day_str = day.isoformat()
        day_rows = by_day.get(day_str, [])
        if day_rows:
            report_path = write_daily_report(day_str, day_rows, daily_dir)
            generated.append(report_path)
            ok_rows = [r for r in day_rows if r.get("health_ok") == "True"]
            dify_rows = [r for r in day_rows if r.get("dify_reachable") == "True"]
            index_rows.append(
                {
                    "date": day_str,
                    "has_snapshot": "1",
                    "snapshot_count": len(day_rows),
                    "health_ok_rate": round(len(ok_rows) / len(day_rows) * 100, 1),
                    "dify_reachable_rate": round(len(dify_rows) / len(day_rows) * 100, 1),
                    "report_file": str(report_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                }
            )
        else:
            index_rows.append(
                {
                    "date": day_str,
                    "has_snapshot": "0",
                    "snapshot_count": 0,
                    "health_ok_rate": "",
                    "dify_reachable_rate": "",
                    "report_file": "",
                }
            )

    with index_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["date", "has_snapshot", "snapshot_count", "health_ok_rate", "dify_reachable_rate", "report_file"],
        )
        writer.writeheader()
        writer.writerows(index_rows)

    total_days = len(index_rows)
    days_with_data = sum(1 for r in index_rows if r["has_snapshot"] == "1")
    print(f"[OK] daily reports generated: {len(generated)}")
    print(f"[OK] daily index csv: {index_csv}")
    print(f"[INFO] calendar days in range {start_date} ~ {end_date}: {total_days}, with data: {days_with_data}, gap days: {total_days - days_with_data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
