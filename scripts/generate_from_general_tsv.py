#!/usr/bin/env python3
"""从通用安全TSV生成知识条目并追加到KB。"""
import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TSV_FILE = REPO_ROOT / "scripts" / "general_safety_entries.tsv"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

SRC_TITLE = "Prudent Practices in the Laboratory (Ch.1): Safety Culture (National Academies Press)"
SRC_ORG = "National Research Council / NIH / NCBI"
SRC_URL = "https://www.ncbi.nlm.nih.gov/books/NBK55882/"
SRC_TYPE = "authoritative_manual"

ID_SEQ = 10450


def next_id():
    global ID_SEQ
    ID_SEQ += 1
    return f"KB-GEN-{ID_SEQ:04d}"


def sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


def parse_tsv(filepath):
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                continue
            entries.append({
                "title": parts[0].strip(), "category": parts[1].strip(),
                "subcategory": parts[2].strip(), "risk": parts[3].strip(),
                "hazard_types": parts[4].strip(), "answer": parts[5].strip(),
            })
    return entries


def generate_question(entry):
    title = entry["title"]
    subcat = entry["subcategory"]
    cat = entry["category"]

    if "应急" in cat:
        question = f"实验室{title}应如何正确应对？"
        scenario = f"应急响应-{title}"
        kb_category = "通用"
        kb_subcategory = "应急处置"
    else:
        question = f"关于{title}，有哪些核心要求和最佳实践？"
        scenario = f"安全制度-{title}"
        kb_category = "通用"
        kb_subcategory = subcat

    return question, scenario, kb_category, kb_subcategory


def enrich(answer):
    ppe = "按具体操作选择相应PPE（护目镜/防化手套/实验服为基础）"
    forbidden = "严禁未经授权人员进入实验室;禁止未查阅SDS即操作化学品;禁止敞口存放危险化学品"
    disposal = "按实验室危废分类规则和机构管理制度处置"
    first_aid = "按具体化学品SDS和伤害类型采取对应急救措施"
    emergency = "按实验室应急预案和机构应急规程执行"
    legal_notes = "参照美国OSHA Laboratory Standard (29 CFR § 1910.1450)和中国教育部实验室安全管理相关规范"
    references = "National Research Council. Prudent Practices in the Laboratory (2011). National Academies Press."
    return ppe, forbidden, disposal, first_aid, emergency, legal_notes, references


def main():
    entries = parse_tsv(TSV_FILE)
    print(f"Parsed {len(entries)} general safety entries")

    existing = []
    if KB_FILE.exists():
        with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
            existing = list(csv.DictReader(f))
    print(f"Existing KB entries: {len(existing)}")

    existing_ids = {r.get("id", "") for r in existing}
    existing_sigs = set()
    for r in existing:
        existing_sigs.add(sig(r.get("title", ""), r.get("question", "")))

    new_rows = []
    for entry in entries:
        question, scenario, kb_category, kb_subcategory = generate_question(entry)
        ppe, forbidden, disposal, first_aid, emergency, legal_notes, references = enrich(entry["answer"])

        row = {
            "id": next_id(), "title": entry["title"],
            "category": kb_category, "subcategory": kb_subcategory,
            "lab_type": "通用", "risk_level": entry["risk"],
            "hazard_types": entry["hazard_types"],
            "scenario": scenario, "question": question,
            "answer": entry["answer"],
            "steps": "了解制度要求;参加安全培训;执行风险评估;遵守操作规程;报告安全隐患;持续学习改进",
            "ppe": ppe, "forbidden": forbidden, "disposal": disposal,
            "first_aid": first_aid, "emergency": emergency,
            "legal_notes": legal_notes, "references": references,
            "source_type": SRC_TYPE, "source_title": SRC_TITLE,
            "source_org": SRC_ORG, "source_version": "2011",
            "source_date": "2011", "source_url": SRC_URL,
            "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft",
            "tags": f"{entry['title']};安全制度;NCBI",
            "language": "zh-CN",
        }
        s = sig(row["title"], row["question"])
        if row["id"] in existing_ids or s in existing_sigs:
            continue
        existing_sigs.add(s)
        existing_ids.add(row["id"])
        new_rows.append(row)

    print(f"Truly new entries: {len(new_rows)}")

    if not new_rows:
        print("No new entries to add.")
        return 0

    all_rows = existing + new_rows
    with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in all_rows:
            clean = {h: row.get(h, "") for h in HEADERS}
            writer.writerow(clean)

    print(f"Done. Total KB entries: {len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
