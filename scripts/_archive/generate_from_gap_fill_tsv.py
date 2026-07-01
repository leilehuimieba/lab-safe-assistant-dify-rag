#!/usr/bin/env python3
"""从缺口补充TSV生成知识条目并追加到KB。"""
import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TSV_FILE = REPO_ROOT / "scripts" / "gap_fill_entries.tsv"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

SRC_TITLE = "Cornell Laboratory Safety Manual & Prudent Practices in the Laboratory"
SRC_ORG = "Cornell University EHS / National Research Council"
SRC_URL = "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual"
SRC_TYPE = "university_manual"

ID_SEQ = 10500


def next_id():
    global ID_SEQ
    ID_SEQ += 1
    return f"KB-GAPF-{ID_SEQ:04d}"


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
    cat = entry["category"]
    subcat = entry["subcategory"]

    if cat == "电气安全":
        question = f"{title}有哪些具体要求？如何确保电气安全？"
        scenario = f"电气安全-{title}"
        kb_category = "电气"
    elif cat == "辐射安全":
        question = f"{title}需要注意哪些事项？如何防护？"
        scenario = f"辐射安全-{title}"
        kb_category = "辐射"
    elif cat == "人体工学":
        question = f"{title}有哪些正确做法和注意事项？"
        scenario = f"人体工学-{title}"
        kb_category = "通用"
    elif cat == "管理制度":
        question = f"关于{title}，有哪些具体规定和最佳实践？"
        scenario = f"管理制度-{title}"
        kb_category = "通用"
    else:
        question = f"{title}的具体要求是什么？有哪些注意事项？"
        scenario = f"{cat}-{title}"
        kb_category = "化学"

    return question, scenario, kb_category, subcat


def enrich(entry):
    answer = entry["answer"]
    title = entry["title"]

    ppe_parts = []
    if re.search(r"护目镜|面罩|眼部|眼睛", answer):
        ppe_parts.append("护目镜/面罩")
    if re.search(r"手套|防化", answer):
        ppe_parts.append("防化手套")
    if re.search(r"实验服|工作服|防护服|实验室服|长袖|围裙", answer):
        ppe_parts.append("实验服/防护服")
    if re.search(r"通风柜|排气", answer):
        ppe_parts.append("通风柜操作")
    if re.search(r"剂量计|监测", answer):
        ppe_parts.append("辐射监测剂量计")
    ppe = ";".join(ppe_parts) if ppe_parts else "按具体操作选择相应PPE"

    forbidden_parts = []
    for pattern in [r"严禁(.*?)(?:[。；;，,]|$)", r"禁止(.*?)(?:[。；;，,]|$)", r"不要(.*?)(?:[。；;，,]|$)"]:
        for m in re.finditer(pattern, answer):
            fb = m.group(0).rstrip("。；;，,")
            if 3 < len(fb) < 100:
                forbidden_parts.append(fb)
    forbidden = ";".join(forbidden_parts[:5]) if forbidden_parts else "按安全规程操作"

    disposal = "按实验室废物分类规章和机构EHS要求处置"
    if re.search(r"危废|危险废物", answer):
        disposal = "按危险废物管理规定分类处置"
    if re.search(r"放射性", answer):
        disposal = "按放射性废物管理规程分类收集和处置"

    first_aid = "按具体危害类型和伤害情况采取对应急救措施并就医"
    if re.search(r"冲洗.*分钟", answer):
        first_aid = "皮肤/眼部接触：大量清水冲洗至少15分钟；全身暴露：立即就医"
    if re.search(r"PEG|聚乙二醇|异丙醇.*皮肤", answer):
        first_aid = "苯酚皮肤暴露：立即用PEG 300/400或异丙醇擦拭污染皮肤区域，然后用大量清水冲洗，立即就医"
    if re.search(r"电击|触电|断电.*急救", answer):
        first_aid = "电击：先断电再接触伤者；检查呼吸脉搏；CPR如需要；立即就医"

    emergency = "按实验室应急预案和机构应急规程执行"
    if re.search(r"EHS|联系EHS|通知", answer):
        emergency = "联系EHS和/或拨打应急电话；必要时疏散；按应急预案执行"
    if re.search(r"不要.*移动|不要.*打开|不要.*触碰|爆炸", answer):
        emergency = "疑似爆炸性物质：不要移动或触碰容器；立即撤离区域并通知EHS"

    legal_notes = "参照美国OSHA/NEC/NFPA/ANSI标准和机构政策；中国等效标准见相关GB系列"
    references = "Cornell University Laboratory Safety Manual; National Research Council Prudent Practices (2011)"

    return ppe, forbidden, disposal, first_aid, emergency, legal_notes, references


def main():
    entries = parse_tsv(TSV_FILE)
    print(f"Parsed {len(entries)} gap-fill entries")

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
        ppe, forbidden, disposal, first_aid, emergency, legal_notes, references = enrich(entry)

        row = {
            "id": next_id(), "title": entry["title"],
            "category": kb_category, "subcategory": kb_subcategory,
            "lab_type": "通用", "risk_level": entry["risk"],
            "hazard_types": entry["hazard_types"],
            "scenario": scenario, "question": question,
            "answer": entry["answer"],
            "steps": "了解相关规程和制度;穿戴适当PPE;按安全规程操作;妥善处置废物;报告异常",
            "ppe": ppe, "forbidden": forbidden, "disposal": disposal,
            "first_aid": first_aid, "emergency": emergency,
            "legal_notes": legal_notes, "references": references,
            "source_type": SRC_TYPE, "source_title": SRC_TITLE,
            "source_org": SRC_ORG, "source_version": "2024",
            "source_date": "2024", "source_url": SRC_URL,
            "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft",
            "tags": f"{entry['title']};{kb_category};Cornell",
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
