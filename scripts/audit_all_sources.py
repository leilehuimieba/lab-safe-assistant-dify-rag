#!/usr/bin/env python3
"""对全部知识库记录进行来源风险评估，输出high_risk清单。"""
import csv
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"

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
            return True, label, p
    return False, '', ''


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

    high_risk_rows = []
    for r in rows:
        flag, label, pattern = is_high_risk(r)
        if flag:
            high_risk_rows.append({
                'row': r,
                'batch': detect_batch(r),
                'label': label,
                'pattern': pattern,
            })

    print(f"总记录数: {len(rows)}")
    print(f"high_risk记录数: {len(high_risk_rows)}")
    print()

    batch_counts = Counter(hr['batch'] for hr in high_risk_rows)
    print("按批次分布:")
    for k, v in batch_counts.most_common():
        print(f"  {k}: {v}")

    print()
    label_counts = Counter(hr['label'] for hr in high_risk_rows)
    print("按风险类型分布:")
    for k, v in label_counts.most_common():
        print(f"  {k}: {v}")

    print()
    print("=== high_risk条目清单 ===")
    for hr in high_risk_rows:
        r = hr['row']
        print(f"{r['id']} | {hr['batch']} | {hr['label']} | {r['title'][:50]} | {r['source_title'][:80]}")

    # 写入移除清单
    out_file = REPO_ROOT / "high_risk_removal_list.csv"
    with out_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "batch", "risk_type", "title", "source_title", "references"])
        writer.writeheader()
        for hr in high_risk_rows:
            r = hr['row']
            writer.writerow({
                "id": r["id"],
                "batch": hr["batch"],
                "risk_type": hr["label"],
                "title": r["title"],
                "source_title": r.get("source_title", ""),
                "references": r.get("references", ""),
            })
    print(f"\n清单已保存: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
