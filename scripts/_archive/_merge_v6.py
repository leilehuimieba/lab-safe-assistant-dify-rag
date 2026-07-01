import csv, json, hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CSV = REPO / "knowledge_base_curated.csv"
JSON = REPO / "scripts" / "kb_batch_data.json"

with open(JSON, encoding="utf-8") as f:
    batch = json.load(f)

with open(CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

fieldnames = list(rows[0].keys())
print(f"Fieldnames: {fieldnames}")

def sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]

existing = {sig(r["title"], r["question"]) for r in rows}

max_id = 0
for r in rows:
    try:
        n = int(r["id"].split("-")[-1])
        if n > max_id:
            max_id = n
    except:
        pass
start = max(max_id + 1, 9000)

new_count = 0
for e in batch:
    s = sig(e["title"], e["question"])
    if s in existing:
        continue

    entry = {f: "N/A" for f in fieldnames}
    entry["id"] = f"KB-BLK-{start:04d}"
    start += 1
    entry["language"] = "zh-CN"
    entry["source_type"] = "guideline"
    entry["source_version"] = "2024"
    entry["source_date"] = "2024-01-01"
    entry["last_updated"] = "2024-01-01"
    entry["reviewer"] = "auto"
    entry["status"] = "draft"

    # Map batch keys to CSV keys
    entry["category"] = e.get("category", "N/A")
    entry["subcategory"] = e.get("subcategory", "N/A")
    entry["lab_type"] = e.get("lab_type", "N/A")
    entry["risk_level"] = e.get("risk_level", "N/A")
    entry["hazard_types"] = e.get("hazard_types", "N/A")
    entry["scenario"] = e.get("scenario", "N/A")
    entry["title"] = e.get("title", "N/A")
    entry["question"] = e.get("question", "N/A")
    entry["answer"] = e.get("answer", "N/A")
    entry["steps"] = e.get("steps", "N/A")
    entry["ppe"] = e.get("ppe", "N/A")
    entry["forbidden"] = e.get("forbidden", "N/A")
    entry["disposal"] = e.get("disposal", "N/A")
    entry["first_aid"] = e.get("first_aid", "N/A")
    entry["emergency"] = e.get("emergency", "N/A")
    entry["source_title"] = e.get("source_title", "N/A")
    entry["source_org"] = e.get("source_org", "N/A")
    entry["source_url"] = e.get("source_url", "N/A")
    entry["tags"] = e.get("tags", "N/A")

    rows.append(entry)
    new_count += 1

with open(CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f"Merged {new_count} new entries. Total: {len(rows)}")
