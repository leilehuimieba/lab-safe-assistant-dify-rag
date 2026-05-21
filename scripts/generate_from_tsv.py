#!/usr/bin/env python3
"""从TSV文件批量生成知识条目。

用法：python scripts/generate_from_tsv.py [tsv_file] [id_start]
TSV格式 (制表符分隔):
中文名	英文名	危害类型	风险等级	特殊注意事项
"""

import csv
import hashlib
import sys
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

DEFAULT_SRC = ("高等学校实验室安全规范（教育部2024）", "教育部",
               "https://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html")

_ID_SEQ = 0


def next_id():
    global _ID_SEQ
    _ID_SEQ += 1
    return f"KB-TSV-{_ID_SEQ}"


def sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


def main():
    tsv_path = sys.argv[1] if len(sys.argv) > 1 else "new_chemicals_combined.tsv"
    tsv_file = Path(tsv_path)
    if not tsv_file.is_absolute():
        tsv_file = REPO_ROOT / "scripts" / tsv_file
    if not tsv_file.exists():
        print(f"Cannot find: {tsv_file}")
        return 1

    global _ID_SEQ
    _ID_SEQ = int(sys.argv[2]) if len(sys.argv) > 2 else 9500

    chemicals = []
    with open(tsv_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 5:
                chemicals.append(tuple(parts[:5]))

    print(f"Loaded {len(chemicals)} chemicals from TSV")

    new_rows = []
    for name, eng, hazards, risk, note in chemicals:
        sn = name.split("/")[0]
        stitle, sorg, surl = DEFAULT_SRC

        new_rows.append({
            "id": next_id(), "category": "化学", "subcategory": "危化品储存",
            "lab_type": "化学", "risk_level": risk, "hazard_types": hazards,
            "scenario": f"{sn}的安全储存",
            "title": f"危化品-{sn}储存",
            "question": f"{sn}应该如何正确储存？",
            "answer": f"{sn}（{eng}）属于{hazards}类化学品。储存要求：存放在阴凉、干燥、通风良好的化学品储存柜中，远离热源/明火/阳光直射。与不相容化学品隔离存放。瓶身贴有清晰标签（品名、浓度、危害标识、日期）。使用后立即盖紧瓶盖。{note}",
            "steps": "确认化学品柜类别;检查瓶身标签和密封;与不相容物分开存放;记录存放位置和数量",
            "ppe": "搬运时佩戴护目镜、实验服、防化手套",
            "forbidden": "禁止敞口存放;禁止与氧化剂/不相容试剂混放;禁止无标签存放;禁止在通风柜外长期存放",
            "disposal": f"过期或废弃{sn}按危废分类处理",
            "first_aid": "皮肤接触：大量清水冲洗;眼睛接触：洗眼器冲洗并就医;吸入：移至通风处",
            "emergency": "大量泄漏：隔离区域，通风，用惰性吸收材料处理",
            "legal_notes": "", "references": "",
            "source_type": "regulatory_standard",
            "source_title": stitle, "source_org": sorg, "source_version": "",
            "source_date": "", "source_url": surl, "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft", "tags": f"{sn};储存;MSDS;{eng}", "language": "zh-CN",
        })

        new_rows.append({
            "id": next_id(), "category": "化学", "subcategory": "应急",
            "lab_type": "化学", "risk_level": risk, "hazard_types": hazards,
            "scenario": f"{sn}泄漏或人员暴露",
            "title": f"应急-{sn}应急处置",
            "question": f"{sn}泄漏了或者溅到身上了怎么处理？",
            "answer": f"{sn}（{eng}）应急处理：泄漏处理——小量泄漏用惰性吸收材料（如蛭石/硅藻土）覆盖并收集到危废袋中;大量泄漏隔离区域、通风、佩戴PPE后收集。人员暴露——皮肤接触：立即脱去污染衣物，用大量清水冲洗至少15分钟;眼睛接触：立即用洗眼器冲洗至少15分钟并就医;吸入：立即转移到通风处。{note}带上该化学品的SDS就医。",
            "steps": "泄漏：停止实验-隔离区域-通风-佩戴PPE-吸收/收集-危废处置;暴露：立即冲洗-脱去污染衣物-就医-报告",
            "ppe": "处理泄漏时：护目镜、防化手套、实验服、必要时面罩和呼吸防护",
            "forbidden": f"禁止徒手处理泄漏;禁止将泄漏物冲入下水道;禁止使用易燃材料（如纸巾）吸附氧化性{sn}泄漏",
            "disposal": "泄漏吸收材料和污染PPE作为危废处置",
            "first_aid": f"按{sn}的SDS急救指引处理;尽快就医",
            "emergency": f"大量{sn}泄漏且超出自身处置能力：立即疏散并报告，拨打119",
            "legal_notes": "", "references": "",
            "source_type": "regulatory_standard",
            "source_title": stitle, "source_org": sorg, "source_version": "",
            "source_date": "", "source_url": surl, "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft", "tags": f"{sn};应急;泄漏;暴露;{eng}", "language": "zh-CN",
        })

        new_rows.append({
            "id": next_id(), "category": "化学", "subcategory": "危化品安全",
            "lab_type": "化学", "risk_level": risk, "hazard_types": hazards,
            "scenario": f"{sn}的实验操作",
            "title": f"危化品-{sn}安全操作",
            "question": f"使用{sn}时需要佩戴什么PPE？有哪些禁止操作？",
            "answer": f"操作{sn}（{eng}）的PPE和安全要求：必须佩戴护目镜、防化手套（查SDS确认手套材质适用性）和实验服。在有通风和工程控制（通风柜/局部排风）的条件下操作。{note}具体要求：1) 实验前查阅SDS了解危险性和急救措施;2) 在通风柜内操作（如适用）;3) 用后立即清洁外壁并盖紧瓶盖。",
            "steps": "查阅SDS;穿戴正确PPE;在通风柜内操作（如需要）;使用最小必要量;用后清洁密封;洗手",
            "ppe": "护目镜;防化手套（查SDS选择合适的材质）;实验服;封闭鞋",
            "forbidden": "禁止无PPE接触;禁止在通风柜外操作（挥发性/有毒品）;禁止敞口放置;禁止与不相容化学品靠近",
            "disposal": f"含{sn}的废液/废物按相应危废类别处置",
            "first_aid": "按SDS指引处理暴露;就医时携带SDS",
            "emergency": "异常情况（泄漏/起火/暴露）：按应急预案处理",
            "legal_notes": "", "references": "",
            "source_type": "regulatory_standard",
            "source_title": stitle, "source_org": sorg, "source_version": "",
            "source_date": "", "source_url": surl, "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft", "tags": f"{sn};PPE;安全操作;{eng}", "language": "zh-CN",
        })

    print(f"Generated {len(new_rows)} entries from {len(chemicals)} chemicals")

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

    print(f"Truly new (after dedup): {len(truly_new)}")

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

    print(f"Total after merge: {len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
