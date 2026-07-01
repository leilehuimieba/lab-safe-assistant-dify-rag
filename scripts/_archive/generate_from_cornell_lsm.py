#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从Cornell LSM TSV生成知识条目并追加到KB。"""
import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TSV_FILE = REPO_ROOT / "scripts" / "cornell_lsm_entries.tsv"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

SRC_TITLE = "Cornell University Laboratory Safety Manual"
SRC_ORG = "Cornell University EHS"
SRC_URL = "https://ehs.cornell.edu/book/export/html/237"
SRC_TYPE = "university_manual"

ID_SEQ = 11000


def next_id():
    global ID_SEQ
    ID_SEQ += 1
    return f"KB-CORNELL-{ID_SEQ:04d}"


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
            if len(parts) < 7:
                continue
            entries.append({
                "title": parts[0].strip(),
                "category": parts[1].strip(),
                "subcategory": parts[2].strip(),
                "risk": parts[3].strip(),
                "hazard_types": parts[4].strip(),
                "answer": parts[5].strip(),
                "question": parts[6].strip(),
            })
    return entries


def extract_ppe(answer):
    parts = []
    if re.search(r"护目镜|goggle|安全眼镜|眼", answer):
        parts.append("护目镜/安全眼镜")
    if re.search(r"面罩|face shield|面部", answer):
        parts.append("面罩")
    if re.search(r"手套|glove", answer):
        parts.append("防化手套")
    if re.search(r"实验服|工作服|lab coat|防护服|围裙|apron|长袖", answer):
        parts.append("实验服/防护服")
    if re.search(r"通风柜|fume hood|排气", answer):
        parts.append("通风柜操作")
    if re.search(r"安全鞋|封闭鞋|closed.?toe|leather shoe", answer):
        parts.append("安全鞋/封闭鞋")
    return ";".join(parts) if parts else "按具体操作选择相应PPE"


def extract_forbidden(answer):
    parts = []
    for pattern in [r"严禁(.*?)(?:[。；;，,.]|$)", r"禁止(.*?)(?:[。；;，,.]|$)",
                    r"不要(.*?)(?:[。；;，,.]|$)", r"绝不(.*?)(?:[。；;，,.]|$)",
                    r"不得(.*?)(?:[。；;，,.]|$)"]:
        for m in re.finditer(pattern, answer):
            fb = m.group(0).rstrip("。；;，,.")
            if 3 < len(fb) < 120:
                parts.append(fb)
    return ";".join(parts[:5]) if parts else "按安全规程操作"


def extract_first_aid(answer):
    if re.search(r"酚|phenol|PEG|聚乙二醇", answer, re.IGNORECASE):
        return "苯酚皮肤暴露：立即用PEG 300/400或异丙醇擦拭;然后大量清水冲洗;立即就医"
    if re.search(r"氟化氢|hydrofluoric|HF|calcium gluconate|葡萄糖酸钙", answer, re.IGNORECASE):
        return "HF暴露：立即用大量水冲洗;涂抹2.5%葡萄糖酸钙凝胶;立即就医"
    if re.search(r"cryogenic|低温|液氮|液氦|冻伤|frostbite", answer):
        return "冻伤：温水复温（不高于40度）;勿揉搓皮肤;吸入冷蒸气：移至新鲜空气处;就医"
    if re.search(r"冲洗.*分|flush.*min|eyewash|洗眼", answer):
        return "皮肤/眼部接触：大量清水冲洗至少15分钟;脱去污染衣物;立即就医"
    return "按具体危害类型采取对应急救措施并就医"


def extract_steps(answer):
    if "储存" in answer or "存放" in answer:
        return "分类化学品;检查兼容性;选择合适储存位置;标签朝外;记录存放位置;定期检查"
    if "应急" in answer or "急救" in answer or "暴露" in answer:
        return "识别紧急情况;启动应急响应;使用应急设备;实施急救措施;联系紧急服务;填写事故报告"
    if "退役" in answer or "搬迁" in answer or "关闭" in answer:
        return "联系EHS;制定退役计划;分类处置化学品/生物/辐射材料;去污清洁;完成检查表;EHS最终审核"
    if "低温" in answer or "液氮" in answer or "液氦" in answer:
        return "使用专用容器;缓慢转移;保持通风;穿戴低温PPE;监测氧气浓度;检查压力释放装置"
    if "通风" in answer:
        return "保持实验室门关闭;注意异常气味和气流;功能变更时通知EHS;温度问题报告Building Coordinator"
    if "人体工学" in answer or "姿势" in answer:
        return "调整设备和工作台;保持中性姿势;定时微休息;任务轮换;视力休息;伸展运动"
    return "了解相关规程;穿戴适当PPE;按安全规程操作;妥善处置废物;报告异常"


def main():
    entries = parse_tsv(TSV_FILE)
    print(f"Parsed {len(entries)} Cornell LSM entries")

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
        rid = next_id()
        answer = entry["answer"]
        title = entry["title"]
        question = entry["question"]
        cat = entry["category"]
        subcat = entry["subcategory"]
        lab_type = "通用" if cat in ("通用", "物理") else ("化学" if cat == "化学" else "通用")

        ppe_val = extract_ppe(answer)
        forbidden_val = extract_forbidden(answer)
        first_aid_val = extract_first_aid(answer)
        steps_val = extract_steps(answer)

        row = {
            "id": rid,
            "title": title,
            "category": cat,
            "subcategory": subcat,
            "lab_type": lab_type,
            "risk_level": entry["risk"],
            "hazard_types": entry["hazard_types"],
            "scenario": title,
            "question": question,
            "answer": answer,
            "steps": steps_val,
            "ppe": ppe_val,
            "forbidden": forbidden_val,
            "disposal": "按实验室废物分类规章和机构EHS要求处置",
            "first_aid": first_aid_val,
            "emergency": "按实验室应急预案和机构应急规程执行",
            "legal_notes": "参照美国OSHA标准和Cornell University EHS政策;中国等效标准见相关GB系列",
            "references": "Cornell University Laboratory Safety Manual; Prudent Practices in the Laboratory (2011)",
            "source_type": SRC_TYPE,
            "source_title": SRC_TITLE,
            "source_org": SRC_ORG,
            "source_version": "2024",
            "source_date": "2024",
            "source_url": SRC_URL,
            "last_updated": TODAY,
            "reviewer": "auto-generate; pending human review",
            "status": "draft",
            "tags": f"{title};{cat};Cornell",
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
