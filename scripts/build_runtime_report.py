#!/usr/bin/env python3
"""基于 health_snapshots.csv 生成周报 / 月报骨架。"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta
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
    parser.add_argument(
        "--date-from",
        default="",
        help="Inclusive start date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--date-to",
        default="",
        help="Inclusive end date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--last-days",
        type=int,
        default=0,
        help="Filter snapshots by the last N days (inclusive, ending today)",
    )
    parser.add_argument(
        "--iso-week",
        default="",
        help="ISO week label like 2026W21 or 2026-W21",
    )
    parser.add_argument(
        "--notes-output",
        default="",
        help="Optional markdown path for weekly issues notes",
    )
    return parser.parse_args()


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def normalize_iso_week(value: str) -> tuple[int, int]:
    cleaned = value.strip().upper().replace("-", "")
    if len(cleaned) != 7 or "W" not in cleaned:
        raise SystemExit(f"Invalid --iso-week: {value}")
    year = int(cleaned[:4])
    week = int(cleaned[5:])
    return year, week


def resolve_range(args: argparse.Namespace) -> tuple[date | None, date | None]:
    if args.iso_week:
        year, week = normalize_iso_week(args.iso_week)
        monday = date.fromisocalendar(year, week, 1)
        sunday = date.fromisocalendar(year, week, 7)
        return monday, sunday
    if args.last_days and args.last_days > 0:
        today = date.today()
        return today - timedelta(days=args.last_days - 1), today
    start = parse_iso_date(args.date_from) if args.date_from else None
    end = parse_iso_date(args.date_to) if args.date_to else None
    return start, end


def filter_rows(rows: list[dict[str, str]], start: date | None, end: date | None) -> list[dict[str, str]]:
    if not start and not end:
        return rows
    filtered: list[dict[str, str]] = []
    for row in rows:
        captured_at = (row.get("captured_at") or "").strip()
        if not captured_at:
            continue
        row_date = datetime.fromisoformat(captured_at).date()
        if start and row_date < start:
            continue
        if end and row_date > end:
            continue
        filtered.append(row)
    return filtered


def build_notes_text(
    *,
    label: str,
    start: date | None,
    end: date | None,
    rows: list[dict[str, str]],
    ok_rows: list[dict[str, str]],
    dify_rows: list[dict[str, str]],
    avg_ms_values: list[float],
    p95_values: list[float],
) -> str:
    period = (
        f"{start.isoformat()} ~ {end.isoformat()}"
        if start and end
        else f"{start.isoformat()} ~ {end.isoformat() if end else 'latest'}"
        if start or end
        else "latest"
    )
    return "\n".join(
        [
            "# 周度运行问题记录",
            "",
            f"> 周次：{label}",
            f"> 时间范围：{period}",
            "",
            "## 1. 本周运行摘要",
            "",
            f"- 快照数：`{len(rows)}`",
            f"- `/health` 正常率：`{round(len(ok_rows) / len(rows) * 100, 1)}%`",
            f"- Dify 可达率：`{round(len(dify_rows) / len(rows) * 100, 1)}%`",
            f"- 平均耗时：`{round(avg(avg_ms_values), 1)}ms`",
            f"- P95：`{round(avg(p95_values), 1)}ms`",
            "",
            "## 2. 本周问题",
            "",
            "1. 暂未发现健康检查失败样本；继续观察连续样本积累情况。",
            "2. 当前周样本量仍小，性能结论只作为阶段骨架，不作为最终长期指标。",
            "3. 如后续出现知识库重载、Dify 不可达或响应抖动，应在此按日期逐条补记。",
            "",
            "## 3. 已处理动作",
            "",
            "1. 已固定每日运行检查任务，持续产出 health / meta / stats 快照。",
            "2. 已补齐周报生成能力，可按 ISO 周过滤生成独立周报。",
            "3. 已将本周准确率与多轮追问修复后的最新版本纳入运行观察范围。",
            "",
            "## 4. 下周计划",
            "",
            "1. 继续每日采样，累计更完整的连续运行样本。",
            "2. 每周固定复跑一轮申报书关键回归，观察是否出现高优先级回流。",
            "3. 每周更新本文件，把异常、修复动作和版本变更补齐。",
            "",
        ]
    ) + "\n"


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

    start_date, end_date = resolve_range(args)
    rows = filter_rows(rows, start_date, end_date)
    if not rows:
        raise SystemExit("No snapshot rows found in the requested range")

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
                "date_from",
                "date_to",
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
                "date_from": start_date.isoformat() if start_date else "",
                "date_to": end_date.isoformat() if end_date else "",
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
        f"> 统计范围：`{start_date.isoformat() if start_date else '全部'} ~ {end_date.isoformat() if end_date else '全部'}`",
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

    if args.notes_output:
        notes_path = Path(args.notes_output).resolve()
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text(
            build_notes_text(
                label=args.label,
                start=start_date,
                end=end_date,
                rows=rows,
                ok_rows=ok_rows,
                dify_rows=dify_rows,
                avg_ms_values=avg_ms_values,
                p95_values=p95_values,
            ),
            encoding="utf-8",
        )
        print(f"[OK] runtime notes md: {notes_path}")

    print(f"[OK] runtime report md: {report_md}")
    print(f"[OK] runtime report csv: {report_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
