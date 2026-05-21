#!/usr/bin/env python3
"""从混合TSV批量生成知识条目 —— 支持化学品、设备和场景。

TSV格式：类型	名称	英文名/类别	危害	风险	备注
类型: chemical | equipment | scenario
"""

import csv
import hashlib
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

SRC = ("高等学校实验室安全规范（教育部2024）", "教育部",
       "https://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html")

_ID_SEQ = 9900


def next_id():
    global _ID_SEQ
    _ID_SEQ += 1
    return f"KB-MIX-{_ID_SEQ}"


def sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


def parse_tsv(filepath):
    """Parse the mixed TSV returning (chemicals, equipments, scenarios)."""
    chemicals = []
    equipments = []
    scenarios = []
    current_section = None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "化学品" in line:
                current_section = "chemical"
                continue
            elif "设备" in line:
                current_section = "equipment"
                continue
            elif "应急" in line or "场景" in line:
                current_section = "scenario"
                continue
            elif line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 5:
                continue

            if current_section == "chemical":
                chemicals.append(tuple(parts[:5]))
            elif current_section == "equipment":
                equipments.append(tuple(parts[:5]))
            elif current_section == "scenario":
                scenarios.append(tuple(parts[:5]))

    return chemicals, equipments, scenarios


def main():
    tsv_file = REPO_ROOT / "scripts" / "more_entries_batch2.tsv"
    if not tsv_file.exists():
        print(f"File not found: {tsv_file}")
        return 1

    chemicals, equipments, scenarios = parse_tsv(tsv_file)
    print(f"Chemicals: {len(chemicals)}, Equipment: {len(equipments)}, Scenarios: {len(scenarios)}")

    new_rows = []
    stitle, sorg, surl = SRC

    # --- Chemical entries (3 per chemical) ---
    for name, eng, hazards, risk, note in chemicals:
        sn = name.split("/")[0]
        for idx, (qtype, q, answer_tpl) in enumerate([
            ("储存", f"{sn}应该如何正确储存？",
             f"{sn}（{eng}）属于{hazards}类化学品。储存要求：存放在阴凉、干燥、通风良好的化学品储存柜中，远离热源/明火/阳光直射。与不相容化学品隔离存放。瓶身贴有清晰标签（品名、浓度、危害标识、日期）。使用后立即盖紧瓶盖。{note}"),
            ("应急", f"{sn}泄漏了或者溅到身上了怎么处理？",
             f"{sn}（{eng}）应急处理：泄漏处理——小量泄漏用惰性吸收材料（如蛭石/硅藻土）覆盖并收集到危废袋中;大量泄漏隔离区域、通风、佩戴PPE后收集。人员暴露——皮肤接触：立即脱去污染衣物，用大量清水冲洗至少15分钟;眼睛接触：立即用洗眼器冲洗至少15分钟并就医;吸入：立即转移到通风处。{note}带上该化学品的SDS就医。"),
            ("安全操作", f"使用{sn}时需要佩戴什么PPE？有哪些禁止操作？",
             f"操作{sn}（{eng}）的PPE和安全要求：必须佩戴护目镜、防化手套（查SDS确认手套材质适用性）和实验服。在有通风和工程控制（通风柜/局部排风）的条件下操作。{note}具体要求：1) 实验前查阅SDS了解危险性和急救措施;2) 在通风柜内操作（如适用）;3) 用后立即清洁外壁并盖紧瓶盖。"),
        ]):
            new_rows.append({
                "id": next_id(), "category": "化学",
                "subcategory": "危化品储存" if qtype == "储存" else ("应急" if qtype == "应急" else "危化品安全"),
                "lab_type": "化学", "risk_level": risk, "hazard_types": hazards,
                "scenario": f"{sn}的{qtype}", "title": f"危化品-{sn}{qtype}",
                "question": q, "answer": answer_tpl,
                "steps": "查阅SDS;按规程操作;穿戴PPE;通风柜操作;记录",
                "ppe": "护目镜;防化手套;实验服;封闭鞋;必要时面罩",
                "forbidden": "禁止无PPE操作;禁止敞口存放;禁止与不相容物混放;禁止通风柜外操作有毒/挥发性化学品",
                "disposal": f"含{sn}废物按危废分类处置",
                "first_aid": "皮肤接触：大量清水冲洗;眼睛：洗眼器冲洗并就医;吸入：移至通风处",
                "emergency": "大量泄漏：隔离区域-通风-疏散-报告",
                "legal_notes": "", "references": "",
                "source_type": "regulatory_standard",
                "source_title": stitle, "source_org": sorg, "source_version": "",
                "source_date": "", "source_url": surl, "last_updated": TODAY,
                "reviewer": "auto-generate; pending human review",
                "status": "draft", "tags": f"{sn};MSDS;{qtype}", "language": "zh-CN",
            })

    # --- Equipment entries (1 per equipment) ---
    for name, etype, hazards, risk, rule in equipments:
        new_rows.append({
            "id": next_id(), "category": "设备安全", "subcategory": etype,
            "lab_type": "通用", "risk_level": risk, "hazard_types": hazards,
            "scenario": f"{name}的安全操作",
            "title": f"设备-{name}安全使用",
            "question": f"{name}的安全操作注意事项是什么？",
            "answer": f"{name}是实验室{etype}。{rule}。主要风险：{hazards}。使用前必须阅读设备SOP并经过培训;使用中按规定佩戴PPE;使用后按规程清洁和关闭。",
            "steps": "阅读SOP;检查设备状态;佩戴适当PPE;按规程操作;用后清洁关闭;记录使用",
            "ppe": "根据设备类型和操作风险选择相应PPE（护目镜/手套/实验服为基础）",
            "forbidden": "禁止未经培训独立操作;禁止绕过安全联锁装置;禁止在设备运行时离开无人值守",
            "disposal": "设备废弃物和配件按制造商说明和实验室废物规则处置",
            "first_aid": "按设备涉及伤害类型处理（烫伤/切割/电击等）",
            "emergency": "设备异常：立即停机-断电-报告-联系厂商维修",
            "legal_notes": "", "references": "",
            "source_type": "regulatory_standard",
            "source_title": stitle, "source_org": sorg, "source_version": "",
            "source_date": "", "source_url": surl, "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft", "tags": f"{name};设备安全;{etype}", "language": "zh-CN",
        })

    # --- Scenario entries (1 per scenario) ---
    for name, stype, hazards, risk, desc in scenarios:
        new_rows.append({
            "id": next_id(), "category": "通用", "subcategory": stype,
            "lab_type": "通用", "risk_level": risk, "hazard_types": hazards,
            "scenario": f"实验室{name}",
            "title": f"通用-实验室{name}",
            "question": f"实验室{name}有哪些安全要求？",
            "answer": f"实验室{name}的安全要点：{desc}",
            "steps": "了解相关SOP;检查设施设备;按规程操作;记录",
            "ppe": "按具体情况选择适当PPE",
            "forbidden": "禁止违反操作规程;禁止未经培训操作;禁止忽视安全警示",
            "disposal": "按实验室废物分类规则处置",
            "first_aid": "按伤害类型处理",
            "emergency": "按实验室应急预案执行",
            "legal_notes": "", "references": "",
            "source_type": "regulatory_standard",
            "source_title": stitle, "source_org": sorg, "source_version": "",
            "source_date": "", "source_url": surl, "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft", "tags": f"{name};{stype}", "language": "zh-CN",
        })

    print(f"New rows generated: {len(new_rows)}")

    # Load existing KB
    existing = []
    if KB_FILE.exists():
        with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
            existing = list(csv.DictReader(f))
    print(f"Existing KB: {len(existing)}")

    existing_ids = {r.get("id", "") for r in existing}
    existing_sigs = set()
    for r in existing:
        existing_sigs.add(sig(r.get("title", ""), r.get("question", "")))

    truly_new = []
    for r in new_rows:
        if r["id"] in existing_ids:
            continue
        s = sig(r["title"], r["question"])
        if s in existing_sigs:
            continue
        existing_sigs.add(s)
        existing_ids.add(r["id"])
        truly_new.append(r)

    print(f"Truly new: {len(truly_new)}")

    if not truly_new:
        print("No new entries to add.")
        return 0

    all_rows = existing + truly_new
    with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in all_rows:
            clean = {h: row.get(h, "") for h in HEADERS}
            writer.writerow(clean)

    print(f"Total: {len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
