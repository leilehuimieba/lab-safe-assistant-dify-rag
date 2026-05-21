#!/usr/bin/env python3
"""从设备安全TSV生成知识条目并追加到KB。"""
import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TSV_FILE = REPO_ROOT / "scripts" / "equipment_safety_entries.tsv"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

SRC_TITLE = "Prudent Practices in the Laboratory (Ch.7): Equipment Safety (National Academies Press)"
SRC_ORG = "National Research Council / NIH / NCBI"
SRC_URL = "https://www.ncbi.nlm.nih.gov/books/NBK55884/"
SRC_TYPE = "authoritative_manual"

ID_SEQ = 10400


def next_id():
    global ID_SEQ
    ID_SEQ += 1
    return f"KB-EQUIP-{ID_SEQ:04d}"


def sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


def parse_equipment_tsv(filepath):
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                continue
            title = parts[0].strip()
            category = parts[1].strip()
            subcategory = parts[2].strip()
            risk = parts[3].strip()
            hazard_types = parts[4].strip()
            answer = parts[5].strip()
            entries.append({
                "title": title, "category": category, "subcategory": subcategory,
                "risk": risk, "hazard_types": hazard_types, "answer": answer,
            })
    return entries


def generate_question(entry):
    title = entry["title"]
    subcat = entry["subcategory"]
    cat = entry["category"]

    if cat in ("PPE",):
        question = f"实验室中{title}的选择和使用要求是什么？"
        scenario = f"个人防护-{title}"
        kb_category = "通用"
        kb_subcategory = "PPE"
    elif cat == "应急设备":
        question = f"实验室{title}应如何配置、维护和使用？"
        scenario = f"应急设备-{title}"
        kb_category = "通用"
        kb_subcategory = "应急设备"
    elif cat == "应急场景":
        question = f"发生{title}时，应如何正确应对？"
        scenario = f"应急响应-{title}"
        kb_category = "通用"
        kb_subcategory = "应急处置"
    else:
        question = f"{title}需要注意哪些安全事项？如何正确操作？"
        scenario = f"设备操作-{title}"
        kb_category = "设备安全"
        kb_subcategory = subcat

    return question, scenario, kb_category, kb_subcategory


def enrich(entry):
    answer = entry["answer"]
    title = entry["title"]

    ppe_parts = []
    if re.search(r"护目镜|面罩|眼部|眼睛", answer):
        ppe_parts.append("护目镜/面罩")
    if re.search(r"手套", answer):
        ppe_parts.append("防化手套")
    if re.search(r"实验服|工作服|防护服|实验室工作服", answer):
        ppe_parts.append("实验服")
    if re.search(r"通风柜|排气", answer):
        ppe_parts.append("通风柜操作")
    if re.search(r"安全鞋|绝缘鞋|钢头鞋|封闭鞋|结实的鞋", answer):
        ppe_parts.append("安全鞋")
    ppe = ";".join(ppe_parts) if ppe_parts else "护目镜;实验服;手套;封闭鞋"

    forbidden_parts = []
    for pattern in [r"严禁(.*?)(?:[。；;]|$)", r"禁止(.*?)(?:[。；;]|$)", r"不要(.*?)(?:[。；;]|$)"]:
        for m in re.finditer(pattern, answer):
            fb = m.group(0).strip("。；;；")
            if 3 < len(fb) < 80:
                forbidden_parts.append(fb)
    forbidden = ";".join(forbidden_parts[:5]) if forbidden_parts else "未经培训不得独立操作;禁止绕过安全联锁装置"

    disposal = "设备废弃物按制造商说明和危废规程处置"
    if re.search(r"危险废物|危废", answer):
        disposal = "受污染部件和材料按危险废物管理规定分类处置"
    if re.search(r"回收", answer):
        disposal += ";可回收部件按回收流程处理"

    first_aid_parts = []
    if re.search(r"洗眼|冲洗.*分钟", answer):
        first_aid_parts.append("眼部接触：立即用洗眼器冲洗至少15分钟并就医")
    if re.search(r"冻伤", answer):
        first_aid_parts.append("冻伤：温水复温，勿揉搓皮肤，就医")
    if re.search(r"烫伤|灼伤|烧伤", answer):
        first_aid_parts.append("烫伤/灼伤：冷水冲洗，覆盖清洁敷料，就医")
    if re.search(r"电击|触电", answer):
        first_aid_parts.append("电击：先断电再接触伤者，检查呼吸脉搏，CPR如需要，立即就医")
    first_aid = ";".join(first_aid_parts) if first_aid_parts else "按伤害类型处理（烫伤/切割/电击/化学暴露），严重时立即就医"

    emergency_parts = []
    if re.search(r"撤离|疏散", answer):
        emergency_parts.append("必要时立即撤离区域人员")
    if re.search(r"灭火器", answer):
        emergency_parts.append("小火使用适当灭火器灭火")
    if re.search(r"火灾报警|拉响", answer):
        emergency_parts.append("立即拉响火灾报警")
    emergency = ";".join(emergency_parts) if emergency_parts else "立即停机断电;通知相关人员;联系EHS;按应急预案执行"

    legal_notes = ""
    if re.search(r"NEC|NFPA|OSHA|ANSI|ASME|DOT|CGA|NRC|EPA", answer):
        legal_notes = "参照美国NEC/NFPA/OSHA/ANSI/DOT等标准框架;中国等效标准见GB系列"

    references = "National Research Council. Prudent Practices in the Laboratory (2011). Chapter 7: Equipment Safety."

    return ppe, forbidden, disposal, first_aid, emergency, legal_notes, references


def main():
    entries = parse_equipment_tsv(TSV_FILE)
    print(f"Parsed {len(entries)} equipment safety entries")

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
            "steps": "阅读设备SOP;检查设备状态;穿戴适当PPE;按规程操作;用后清洁关闭;记录使用",
            "ppe": ppe, "forbidden": forbidden, "disposal": disposal,
            "first_aid": first_aid, "emergency": emergency,
            "legal_notes": legal_notes, "references": references,
            "source_type": SRC_TYPE, "source_title": SRC_TITLE,
            "source_org": SRC_ORG, "source_version": "2011",
            "source_date": "2011", "source_url": SRC_URL,
            "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft",
            "tags": f"{entry['title']};设备安全;NCBI",
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
