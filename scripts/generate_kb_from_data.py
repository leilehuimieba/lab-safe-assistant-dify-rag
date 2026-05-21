#!/usr/bin/env python3
"""从结构化数据生成知识条目 — 直接写入 CSV，避免引号转义问题。

数据格式 (TSV-like, 用 | 分隔):
category|subcategory|lab_type|risk_level|hazard_types|scenario|title|question|answer|steps|ppe|forbidden|disposal|first_aid|emergency|source_title|source_org|source_url|tags

用法：python scripts/generate_kb_from_data.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

CORNELL = "Cornell Laboratory Safety Manual"
CORNELL_URL = "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual"
OSHA = "OSHA 29 CFR 1910.1450"
NIH = "NIH Chemical Safety Guidelines"
NFPA = "NFPA Standards"
CDC = "CDC/NIH BMBL"
GB_STD = "GB 19489/GB 13690/GB 18597"


def load_data():
    """Load structured entries from a JSON file (cleaner than embedding in Python)."""
    data_file = REPO_ROOT / "scripts" / "kb_batch_data.json"
    if data_file.exists():
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


def main():
    entries = load_data()
    if not entries:
        print("No entries found in kb_batch_data.json")
        return 1

    print(f"Loaded {len(entries)} entries from JSON")

    _id_seq = 9000

    existing = []
    if KB_FILE.exists():
        with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
            existing = list(csv.DictReader(f))
    print(f"Existing KB entries: {len(existing)}")

    existing_ids = {r.get("id", "") for r in existing}
    existing_sigs = set()
    for r in existing:
        existing_sigs.add(_sig(r.get("title", ""), r.get("question", "")))

    new_rows = []
    for e in entries:
        _id_seq += 1
        rid = f"KB-BLK-{_id_seq}"
        if rid in existing_ids:
            continue
        s = _sig(e.get("title", ""), e.get("question", ""))
        if s in existing_sigs:
            continue
        existing_sigs.add(s)

        row = {
            "id": rid,
            "title": e.get("title", ""),
            "category": e.get("category", ""),
            "subcategory": e.get("subcategory", ""),
            "lab_type": e.get("lab_type", ""),
            "risk_level": e.get("risk_level", "2"),
            "hazard_types": e.get("hazard_types", ""),
            "scenario": e.get("scenario", ""),
            "question": e.get("question", ""),
            "answer": e.get("answer", ""),
            "steps": e.get("steps", ""),
            "ppe": e.get("ppe", ""),
            "forbidden": e.get("forbidden", ""),
            "disposal": e.get("disposal", ""),
            "first_aid": e.get("first_aid", ""),
            "emergency": e.get("emergency", ""),
            "legal_notes": "",
            "references": "",
            "source_type": "public_authoritative_source",
            "source_title": e.get("source_title", ""),
            "source_org": e.get("source_org", ""),
            "source_version": "",
            "source_date": "",
            "source_url": e.get("source_url", ""),
            "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft",
            "tags": e.get("tags", ""),
            "language": "zh-CN",
        }
        new_rows.append(row)

    print(f"Truly new: {len(new_rows)}")

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

    print(f"Total after merge: {len(all_rows)}")

    cats = {}
    for r in all_rows:
        c = r.get("category", "unknown")
        cats[c] = cats.get(c, 0) + 1
    print(f"Category distribution: {json.dumps(cats, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
