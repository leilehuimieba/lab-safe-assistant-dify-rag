#!/usr/bin/env python3
"""删除untraceable和medium_risk的KB-NEW记录。"""
import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
REPORT_FILE = REPO_ROOT / "untraceable_medium_removal_report.md"
LIST_FILE = REPO_ROOT / "untraceable_medium_removal_list.csv"
TODAY = datetime.now().strftime("%Y-%m-%d")

high_risk_patterns = [
    r'blog\.', r'chempedia', r'crazyforchem', r'cprcertificationnow',
    r'tjtywh', r'ziebaq', r'bisonlife', r'ifixit',
    r'researchgate', r'durpro', r'laboao', r'kintek',
    r'files-do-not-link', r'benchchem',
]


def assess(row):
    if not row['id'].startswith('KB-NEW'):
        return 'keep'
    text = (row.get('source_title', '') + ' ' + row.get('references', '') + ' ' + row.get('source_url', '')).lower()
    for p in high_risk_patterns:
        if re.search(p, text, re.I):
            return 'high_risk'  # 理论上已被清理
    has_url = bool(re.search(r'https?://', text))
    has_org = bool(row.get('source_org', '').strip())
    if not has_url and not has_org:
        return 'untraceable'
    if not has_url:
        if any(x in text for x in ['manual', 'handbook', 'guide', 'sop', 'standard', 'regulation', 'code']):
            return 'low_risk'
        return 'medium_risk'
    return 'low_risk'


def main():
    with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    keep_rows = []
    remove_rows = []
    for r in rows:
        result = assess(r)
        if result in ('untraceable', 'medium_risk'):
            batch = r.get('tags', '').split(';')[0] if r.get('tags') else 'KB-NEW'
            remove_rows.append({
                'row': r,
                'batch': batch,
                'reason': result,
            })
        else:
            keep_rows.append(r)

    print(f"Total: {len(rows)}")
    print(f"Remove (untraceable+medium): {len(remove_rows)}")
    print(f"Remaining: {len(keep_rows)}")

    # 统计
    batch_counts = Counter(hr['batch'] for hr in remove_rows)
    reason_counts = Counter(hr['reason'] for hr in remove_rows)

    # 写回知识库
    with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in keep_rows:
            writer.writerow(row)

    # 写入移除清单
    with LIST_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "batch", "reason", "title", "category", "subcategory", "source_title", "source_org", "references"])
        writer.writeheader()
        for hr in remove_rows:
            r = hr['row']
            writer.writerow({
                "id": r["id"],
                "batch": hr["batch"],
                "reason": hr["reason"],
                "title": r["title"],
                "category": r.get("category", ""),
                "subcategory": r.get("subcategory", ""),
                "source_title": r.get("source_title", ""),
                "source_org": r.get("source_org", ""),
                "references": r.get("references", ""),
            })

    # 生成报告
    report_lines = [
        "# Untraceable + Medium-Risk 来源移除报告",
        "",
        f"**执行时间**: {TODAY}",
        f"**操作**: 删除所有无URL无机构（untraceable）和无URL且描述模糊（medium_risk）的KB-NEW记录",
        "",
        "## 统计",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 移除前总记录 | {len(rows)} |",
        f"| 移除记录数 | {len(remove_rows)} |",
        f"| 移除后总记录 | {len(keep_rows)} |",
        "",
        "## 按原因分布",
        "",
    ]
    for k, v in reason_counts.most_common():
        report_lines.append(f"- {k}: {v}")
    report_lines.append("")
    report_lines.append("## 按批次分布")
    report_lines.append("")
    for k, v in batch_counts.most_common():
        report_lines.append(f"- {k}: {v}")
    report_lines.append("")
    report_lines.append("## 移除清单（前50条）")
    report_lines.append("")
    report_lines.append("| ID | 批次 | 原因 | 分类 | 标题 |")
    report_lines.append("|----|------|------|------|------|")
    for hr in remove_rows[:50]:
        r = hr['row']
        report_lines.append(f"| {r['id']} | {hr['batch']} | {hr['reason']} | {r.get('category','')}-{r.get('subcategory','')[:20]} | {r['title'][:50]} |")
    report_lines.append("")

    with REPORT_FILE.open("w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nRemoval list: {LIST_FILE}")
    print(f"Report: {REPORT_FILE}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
