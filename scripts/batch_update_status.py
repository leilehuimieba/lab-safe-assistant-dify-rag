#!/usr/bin/env python3
"""根据审核结果批量更新知识库状态。"""
import csv
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TODAY = datetime.now().strftime("%Y-%m-%d")


def main(audit_csv_path):
    audit_path = Path(audit_csv_path)
    if not audit_path.exists():
        print(f"ERROR: {audit_path} not found")
        return 1

    # 读取审核结果
    audit_map = {}
    with audit_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            kb_id = row.get("kb_id", "").strip()
            result = row.get("audit_result", "").strip().lower()
            score = row.get("total_score", "").strip()
            comment = row.get("audit_comment", "").strip()
            if not kb_id:
                continue
            audit_map[kb_id] = {
                "result": result,
                "score": score,
                "comment": comment,
            }

    print(f"读取到审核记录: {len(audit_map)}")

    # 读取知识库
    with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    updated = 0
    skipped = 0
    for row in rows:
        kb_id = row.get("id", "").strip()
        if kb_id not in audit_map:
            continue

        audit = audit_map[kb_id]
        result = audit["result"]

        if result in ("pass", "pass_after_fix"):
            row["status"] = "reviewed"
            row["last_updated"] = TODAY
            if not row.get("reviewer") or "auto-ingest" in row.get("reviewer", ""):
                row["reviewer"] = "human-audit"
            updated += 1
        elif result == "reject":
            # 标记为待删除，不直接删除以便追溯
            row["status"] = "rejected"
            row["last_updated"] = TODAY
            row["reviewer"] = "human-audit"
            updated += 1
        else:
            skipped += 1

    print(f"更新为 reviewed: {updated}")
    print(f"未处理(needs_revision或其他): {skipped}")

    # 写回
    with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"已保存到: {KB_FILE}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_update_status.py <audit_sample.csv>")
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
