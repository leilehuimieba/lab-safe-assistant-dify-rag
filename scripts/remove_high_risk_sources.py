#!/usr/bin/env python3
"""识别并删除知识库中来源为博客/内容农场/已失效的high_risk记录。"""
import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
REPORT_FILE = REPO_ROOT / "high_risk_removal_report.md"
LIST_FILE = REPO_ROOT / "high_risk_removal_list.csv"
TODAY = datetime.now().strftime("%Y-%m-%d")

high_risk_patterns = [
    (r'blog\.', '博客/内容农场'),
    (r'chempedia', '化学百科(非权威)'),
    (r'crazyforchem', '化学博客(非权威)'),
    (r'cprcertificationnow', '急救培训博客'),
    (r'tjtywh', '未知商业网站'),
    (r'ziebaq', '未知博客'),
    (r'bisonlife', '未知商业PDF'),
    (r'ifixit', '维修社区'),
    (r'researchgate', '学术社交(需登录)'),
    (r'durpro', '商业博客(已失效)'),
    (r'laboao', '设备厂商(已失效)'),
    (r'kintek', '设备厂商(403)'),
    (r'files-do-not-link', '明确不可链接'),
    (r'benchchem', '化学博客(404)'),
]


def is_high_risk(row):
    text = (row.get('source_title', '') + ' ' + row.get('references', '') + ' ' + row.get('source_url', '')).lower()
    for p, label in high_risk_patterns:
        if re.search(p, text, re.I):
            return True, label
    return False, ''


def detect_batch(row):
    rid = row.get('id', '')
    if rid.startswith('KB-NEW'):
        return row.get('tags', '').split(';')[0] if row.get('tags') else 'KB-NEW'
    if rid.startswith('KB-GEN'):
        return 'KB-GEN'
    if rid.startswith('WEB'):
        return 'WEB'
    if rid.startswith('KB-'):
        return 'KB-ORIGINAL'
    return 'OTHER'


def main():
    with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    keep_rows = []
    remove_rows = []
    for r in rows:
        flag, label = is_high_risk(r)
        if flag:
            remove_rows.append({
                'row': r,
                'batch': detect_batch(r),
                'label': label,
            })
        else:
            keep_rows.append(r)

    print(f"Total records: {len(rows)}")
    print(f"High-risk to remove: {len(remove_rows)}")
    print(f"Remaining: {len(keep_rows)}")

    # 统计
    batch_counts = Counter(hr['batch'] for hr in remove_rows)
    label_counts = Counter(hr['label'] for hr in remove_rows)

    # 写入移除清单
    with LIST_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "batch", "risk_type", "title", "source_title", "references"])
        writer.writeheader()
        for hr in remove_rows:
            r = hr['row']
            writer.writerow({
                "id": r["id"],
                "batch": hr["batch"],
                "risk_type": hr["label"],
                "title": r["title"],
                "source_title": r.get("source_title", ""),
                "references": r.get("references", ""),
            })

    # 写回知识库
    with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in keep_rows:
            writer.writerow(row)

    # 生成报告
    report_lines = [
        "# High-Risk 来源移除报告",
        "",
        f"**执行时间**: {TODAY}",
        f"**操作**: 删除来源为博客/内容农场/已失效网站/需登录平台的记录",
        "",
        "## 统计",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 移除前总记录 | {len(rows)} |",
        f"| 移除记录数 | {len(remove_rows)} |",
        f"| 移除后总记录 | {len(keep_rows)} |",
        "",
        "## 按批次分布",
        "",
    ]
    for k, v in batch_counts.most_common():
        report_lines.append(f"- {k}: {v}")
    report_lines.append("")
    report_lines.append("## 按风险类型分布")
    report_lines.append("")
    for k, v in label_counts.most_common():
        report_lines.append(f"- {k}: {v}")
    report_lines.append("")
    report_lines.append("## 移除清单")
    report_lines.append("")
    report_lines.append("| ID | 批次 | 风险类型 | 标题 |")
    report_lines.append("|----|------|----------|------|")
    for hr in remove_rows:
        r = hr['row']
        report_lines.append(f"| {r['id']} | {hr['batch']} | {hr['label']} | {r['title'][:60]} |")
    report_lines.append("")

    with REPORT_FILE.open("w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nRemoval list: {LIST_FILE}")
    print(f"Report: {REPORT_FILE}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
