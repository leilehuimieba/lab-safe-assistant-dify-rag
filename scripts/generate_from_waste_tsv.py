#!/usr/bin/env python3
"""从危废管理TSV生成知识条目并追加到KB。"""
import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TSV_FILE = REPO_ROOT / "scripts" / "waste_management_entries.tsv"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

SRC_TITLE = "Cornell Hazardous Waste Manual (EHS Cornell University)"
SRC_ORG = "Cornell University EHS"
SRC_URL = "https://ehs.cornell.edu/book/export/html/1261"
SRC_TYPE = "university_manual"

ID_SEQ = 10200


def next_id():
    global ID_SEQ
    ID_SEQ += 1
    return f"KB-WASTE-{ID_SEQ:04d}"


def sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


def parse_waste_tsv(filepath):
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
            lab_type = parts[2].strip() if len(parts) > 2 else "通用"
            risk = parts[3].strip() if len(parts) > 3 else "2"
            hazard_types = parts[4].strip() if len(parts) > 4 else ""
            answer = parts[5].strip() if len(parts) > 5 else ""
            entries.append({
                "title": title, "category": category, "lab_type": lab_type,
                "risk": risk, "hazard_types": hazard_types, "answer": answer,
            })
    return entries


def generate_question_answer(entry):
    """从标题和答案内容生成合理的问答对"""
    title = entry["title"]
    answer = entry["answer"]

    # 根据类别和标题生成不同类型的问题
    if entry["category"] in ("制度", "管理制度"):
        question = f"关于{title}，有哪些管理规范和要求？"
        subcategory = "危废制度"
        scenario = f"危废管理-{title}"
    elif entry["category"] == "分类":
        question = f"什么是{title}？如何进行分类管理？"
        subcategory = "危废分类"
        scenario = f"危废分类-{title}"
    elif entry["category"] in ("危废处置", "操作规范"):
        question = f"{title}的具体要求和操作规范是什么？"
        subcategory = "危废处置" if "处置" in entry["category"] or "处置" in title else "危废操作"
        scenario = f"危废操作-{title}"
    else:
        question = f"关于{title}，需要了解哪些安全要求？"
        subcategory = "危废综合"
        scenario = f"危废-{title}"

    return question, subcategory, scenario


def enrich_entry(entry):
    """根据内容添加 steps, ppe, forbidden, disposal, first_aid, emergency 等字段"""
    answer = entry["answer"]

    # PPE 检测
    ppe_parts = []
    if re.search(r"实验服|防护服|工作服", answer):
        ppe_parts.append("实验服")
    if re.search(r"手套", answer):
        ppe_parts.append("防化手套")
    if re.search(r"护目镜|面罩|眼", answer):
        ppe_parts.append("护目镜/面罩")
    if re.search(r"通风柜", answer):
        ppe_parts.append("通风柜操作")
    if re.search(r"封闭鞋|安全鞋", answer):
        ppe_parts.append("封闭鞋")
    ppe = ";".join(ppe_parts) if ppe_parts else "按具体操作选择相应PPE（护目镜/防化手套/实验服为基础）"

    # forbidden
    forbidden_parts = []
    if re.search(r"严禁|禁止", answer):
        for m in re.finditer(r"(?:严禁|禁止)([^。；;]*)", answer):
            fb = m.group(0).strip("。；;；")
            if len(fb) < 60:
                forbidden_parts.append(fb)
    if re.search(r"不要", answer):
        for m in re.finditer(r"不要([^。；;]*)", answer):
            forbidden_parts.append("不要" + m.group(1).strip("。；;；"))
    forbidden = ";".join(forbidden_parts[:5]) if forbidden_parts else "按危废管理规程操作"

    # disposal
    disposal_parts = []
    if re.search(r"危废|危险废物", answer):
        disposal_parts.append("按危险废物管理规定分类处置")
    if re.search(r"回收", answer):
        disposal_parts.append("可回收部分按回收流程处理")
    if re.search(r"下水道|排放", answer):
        disposal_parts.append("严禁倒入下水道或排入环境")
    disposal = ";".join(disposal_parts) if disposal_parts else "按危废规程处置"

    # first_aid
    first_aid_parts = []
    if re.search(r"冲洗|清水", answer):
        first_aid_parts.append("皮肤/眼睛接触：大量清水冲洗至少15分钟")
    if re.search(r"就医|医疗|医生|健康中心", answer):
        first_aid_parts.append("及时就医")
    if re.search(r"葡萄糖酸钙", answer):
        first_aid_parts.append("HF暴露：使用葡萄糖酸钙凝胶")
    if re.search(r"911|拨打", answer):
        first_aid_parts.append("紧急情况拨打911")
    if re.search(r"离开|转移|通风", answer):
        first_aid_parts.append("吸入暴露：移至通风处")
    first_aid = ";".join(first_aid_parts) if first_aid_parts else "按具体化学品SDS急救措施处理"

    # emergency
    emergency_parts = []
    if re.search(r"EHS|联系EHS|通知EHS", answer):
        emergency_parts.append("联系EHS专业人员处置")
    if re.search(r"911|拨打911", answer):
        emergency_parts.append("紧急情况拨打911")
    if re.search(r"疏散|撤离", answer):
        emergency_parts.append("必要时疏散区域人员")
    if re.search(r"不要.*移动|不要.*打开|不要.*触碰", answer):
        emergency_parts.append("疑似爆炸性/反应性废物：不要移动容器，立即通知EHS")
    emergency = ";".join(emergency_parts) if emergency_parts else "联系EHS按应急预案处理"

    # legal_notes and references
    legal_notes = ""
    if re.search(r"RCRA|EPA|DEC|DOT", answer):
        legal_notes = "参照美国RCRA法规框架;中国等效法规见《危险废物名录》"

    references = "Cornell University Hazardous Waste Manual; RCRA Subtitle C; 40 CFR Parts 260-273"

    return ppe, forbidden, disposal, first_aid, emergency, legal_notes, references


def main():
    entries = parse_waste_tsv(TSV_FILE)
    print(f"Parsed {len(entries)} waste management entries from TSV")

    # Load existing KB
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
        question, subcategory, scenario = generate_question_answer(entry)
        ppe, forbidden, disposal, first_aid, emergency, legal_notes, references = enrich_entry(entry)

        row = {
            "id": next_id(), "title": entry["title"],
            "category": "化学", "subcategory": subcategory,
            "lab_type": entry["lab_type"], "risk_level": entry["risk"],
            "hazard_types": entry["hazard_types"],
            "scenario": scenario, "question": question,
            "answer": entry["answer"],
            "steps": "了解相关法规制度;按规程分类和标记;穿戴适当PPE;联系EHS安排处置",
            "ppe": ppe, "forbidden": forbidden, "disposal": disposal,
            "first_aid": first_aid, "emergency": emergency,
            "legal_notes": legal_notes, "references": references,
            "source_type": SRC_TYPE, "source_title": SRC_TITLE,
            "source_org": SRC_ORG, "source_version": "",
            "source_date": "", "source_url": SRC_URL,
            "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft",
            "tags": f"{entry['title']};危废管理;Cornell",
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
