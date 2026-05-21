#!/usr/bin/env python3
"""将新收集的JSON实验室安全数据转换并追加到知识库CSV中。"""
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
NEW_DATA_FILE = REPO_ROOT / ".tmp_new_data" / "实验室安全数据库_整合版.json"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

# 分类映射: 新数据 category -> 现有知识库 category
CATEGORY_MAP = {
    "大型分析仪器": "设备安全",
    "通用物理设备": "设备安全",
    "样品前处理设备": "设备安全",
    "生物类设备": "设备安全",
    "共用设施设备": "设备安全",
    "辐射安全": "辐射",
    "激光安全": "物理",
    "电气安全": "电气",
    "机械安全": "物理",
    "危废处置": "废弃物",
    "化学品SDS": "化学",
    "特定危害类型": "化学",
    "实验室场景化应急": "通用",
    "PPE专题深化": "通用",
    "培训体系": "培训",
    "管理制度": "通用",
    "通用安全": "通用",
    "标准法规": "标准",
    "高校手册": "通用",
    "绿色化学": "化学",
    "通用指南": "通用",
}

# lab_type 推断
LAB_TYPE_MAP = {
    "设备安全": "通用",
    "辐射": "物理",
    "物理": "物理",
    "电气": "电气",
    "废弃物": "化学",
    "化学": "化学",
    "通用": "通用",
    "培训": "通用",
    "标准": "通用",
    "生物": "生物",
}

# 风险等级推断关键词
RISK_KEYWORDS = {
    5: ["爆炸", "死亡", "致命", "剧毒", "氰化物", "自燃", "立即危及生命", "IDLH"],
    4: ["火灾", "高压", "触电", "放射性", "辐射", "激光", "腐蚀", "强酸", "强碱", "强氧化", "强还原", "高温", "窒息"],
    3: ["易燃", "有毒", "有害气体", "泄漏", "烫伤", "灼伤", "割伤", "刺伤", "感染", "生物污染"],
    2: ["刺激性", "挥发性", "噪音", "粉尘", "滑倒", "绊倒"],
    1: ["标识", "培训", "检查", "记录", "清洁", "整理"],
}

ID_SEQ = 0


def next_id():
    global ID_SEQ
    ID_SEQ += 1
    return f"KB-NEW-{ID_SEQ:04d}"


def sig(title, question):
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


def infer_risk_level(text):
    text = text.lower()
    for level, keywords in sorted(RISK_KEYWORDS.items(), reverse=True):
        for kw in keywords:
            if kw in text:
                return str(level)
    return "3"


def join_array(val, sep=";"):
    if isinstance(val, list):
        return sep.join(str(x) for x in val if x)
    return str(val) if val else ""


def generate_question(title, category, subcategory):
    title = str(title).strip()
    cat = str(category).strip()
    sub = str(subcategory).strip()

    if "应急" in cat or "应急" in sub or "应急" in title:
        if "怎么办" in title or "怎么" in title:
            return title
        if "PPE" in title or "防护" in title:
            return f"{title}有哪些要求？"
        return f"实验室{title}应如何应急处置？"

    if "PPE" in cat or "手套" in title or "护目镜" in title or "呼吸防护" in title or "实验服" in title or "面罩" in title or "听力防护" in title or "防静电" in title:
        return f"{title}有哪些要求和注意事项？"

    if "培训" in cat or "制度" in cat or "管理" in cat:
        return f"关于{title}，有哪些规定和要求？"

    if "标准" in cat or "法规" in cat:
        return f"{title}的主要内容是什么？"

    if "废" in cat or "废" in sub or "处置" in title or "SDS" in sub:
        return f"{title}应如何安全处理？"

    if "辐射" in cat or "放射性" in title or "核素" in title:
        return f"{title}的防护要求是什么？"

    if "激光" in cat or "激光" in title:
        return f"{title}的安全要求有哪些？"

    if "电气" in cat or "触电" in title or "电" in title:
        return f"{title}应如何安全操作？"

    if "机械" in cat or "压力容器" in title or "真空" in title:
        return f"{title}有哪些安全注意事项？"

    if "设备" in cat or "仪器" in cat:
        return f"{title}的安全操作规程是什么？"

    return f"关于{title}，有哪些安全要求和注意事项？"


def generate_scenario(title, category, subcategory):
    cat = str(category).strip()
    sub = str(subcategory).strip()
    if "应急" in cat or "应急" in sub:
        return f"应急响应-{title}"
    if "PPE" in cat:
        return f"个人防护-{title}"
    if "培训" in cat or "制度" in cat:
        return f"管理制度-{title}"
    if "标准" in cat:
        return f"标准法规-{title}"
    if "设备" in cat or "仪器" in cat:
        return f"设备操作-{title}"
    if "危废" in cat or "废" in sub:
        return f"废物处置-{title}"
    return f"安全操作-{title}"


def build_answer(entry):
    parts = []

    for key in ["description", "content", "chemical_info"]:
        val = entry.get(key)
        if val:
            parts.append(str(val).strip())

    hazards = entry.get("hazards")
    if hazards and isinstance(hazards, list) and len(hazards) > 0:
        parts.append("主要危害：" + "；".join(hazards))

    for key in ["safety_measures", "controls", "requirements", "key_points"]:
        val = entry.get(key)
        if val and isinstance(val, list) and len(val) > 0:
            parts.append("安全措施：" + "；".join(val))
        elif val and isinstance(val, str) and val.strip():
            parts.append(str(val).strip())

    req = entry.get("requirement")
    if req and isinstance(req, str) and req.strip():
        parts.append("要求：" + req.strip())

    resp = entry.get("responsibilities")
    if resp and isinstance(resp, list) and len(resp) > 0:
        parts.append("职责：" + "；".join(resp))
    elif resp and isinstance(resp, str) and resp.strip():
        parts.append("职责：" + resp.strip())

    prohib = entry.get("prohibitions")
    if prohib and isinstance(prohib, list) and len(prohib) > 0:
        parts.append("禁止事项：" + "；".join(prohib))
    elif prohib and isinstance(prohib, str) and prohib.strip():
        parts.append("禁止事项：" + prohib.strip())

    scope = entry.get("scope")
    if scope and isinstance(scope, str) and scope.strip():
        parts.append("适用范围：" + scope.strip())

    clause = entry.get("clause_reference")
    if clause and isinstance(clause, str) and clause.strip():
        parts.append("条款引用：" + clause.strip())

    for key in ["regulatory_reference", "reference"]:
        val = entry.get(key)
        if val and isinstance(val, str) and val.strip():
            parts.append("法规依据：" + val.strip())

    emerg = entry.get("emergency")
    if emerg and isinstance(emerg, str) and emerg.strip():
        parts.append("应急处置：" + emerg.strip())

    if not parts:
        return "请参照相关安全规范和实验室管理制度执行。"

    return "\n".join(parts)


def build_steps(entry):
    procedures = entry.get("procedures")
    if procedures and isinstance(procedures, dict):
        parts = []
        mapping = {
            "pre_operation": "操作前",
            "operation": "操作中",
            "post_operation": "操作后",
            "maintenance": "维护保养",
        }
        for key, label in mapping.items():
            val = procedures.get(key)
            if val and isinstance(val, list) and len(val) > 0:
                parts.append(f"{label}：" + "；".join(val))
        if parts:
            return "\n".join(parts)

    steps = entry.get("steps")
    if steps and isinstance(steps, list) and len(steps) > 0:
        return "；".join(steps)
    if steps and isinstance(steps, str) and steps.strip():
        return steps.strip()

    return ""


def build_ppe(entry):
    ppe = entry.get("ppe")
    if ppe and isinstance(ppe, list) and len(ppe) > 0:
        return "；".join(ppe)
    if ppe and isinstance(ppe, str) and ppe.strip():
        return ppe.strip()

    cat = str(entry.get("category", "")).strip()
    sub = str(entry.get("subcategory", "")).strip()
    if "辐射" in cat or "放射性" in sub:
        return "个人剂量计；防护手套；实验服"
    if "激光" in cat:
        return "激光护目镜；实验服"
    if "电气" in cat:
        return "绝缘手套；绝缘鞋；护目镜"
    if "生物" in cat:
        return "手套；口罩；护目镜；实验服"
    if "PPE" in cat:
        return "根据具体场景选择相应PPE"
    return "护目镜；实验服；防护手套"


def build_forbidden(entry):
    prohib = entry.get("prohibitions")
    if prohib and isinstance(prohib, list) and len(prohib) > 0:
        return "；".join(prohib)
    if prohib and isinstance(prohib, str) and prohib.strip():
        return prohib.strip()

    cat = str(entry.get("category", "")).strip()
    if "辐射" in cat:
        return "禁止无授权操作放射性物质；禁止用口吸液管操作；禁止在辐射区域饮食"
    if "激光" in cat:
        return "禁止直视激光束；禁止佩戴反射性饰品进入激光区；禁止未经授权调整光路"
    if "电气" in cat:
        return "禁止湿手操作电气设备；禁止带电插拔；禁止擅自拆解电气设备"
    if "危废" in cat or "废" in cat:
        return "禁止随意丢弃废物；禁止将不相容废物混合；禁止无标签存放废物"
    if "应急" in cat:
        return "禁止盲目冒险施救；禁止隐瞒事故不报"
    return "禁止未培训上岗；禁止违反操作规程；禁止擅自移除安全装置"


def build_disposal(entry):
    cat = str(entry.get("category", "")).strip()
    sub = str(entry.get("subcategory", "")).strip()
    if "辐射" in cat or "放射性" in sub:
        return "按放射性废物分类收集，短半衰期衰变贮存，长半衰期移交有资质单位处置"
    if "生物" in cat:
        return "按生物安全等级进行灭活处理后，分类收集交由合规处置"
    if "危废" in cat or "废" in sub or "处置" in sub:
        return "按危废类别分类收集、标识清晰，交由有资质单位合规处置"
    if "化学品" in cat or "SDS" in sub:
        return "按MSDS和实验室危废管理制度分类收集处置"
    return "按实验室废弃物分类管理制度收集处置"


def build_first_aid(entry):
    cat = str(entry.get("category", "")).strip()
    sub = str(entry.get("subcategory", "")).strip()
    if "辐射" in cat or "放射性" in sub:
        return "发生污染立即撤离并报告，按辐射应急预案处理，必要时就医"
    if "激光" in cat:
        return "眼睛受伤立即就医，皮肤灼伤用冷水冲洗并就医"
    if "电气" in cat:
        return "触电时先断电再施救，必要时进行心肺复苏并立即就医"
    if "化学" in cat or "SDS" in sub:
        return "按具体化学品MSDS采取对应急救措施，必要时就医"
    if "生物" in cat:
        return "暴露后立即冲洗并报告，按生物安全应急预案处理并就医"
    return "发生伤害立即停止操作，按具体情况采取急救措施并就医"


def build_emergency(entry):
    emerg = entry.get("emergency")
    if emerg and isinstance(emerg, str) and emerg.strip():
        return emerg.strip()
    cat = str(entry.get("category", "")).strip()
    if "辐射" in cat:
        return "启动辐射应急预案，封锁区域并报告辐射安全官"
    if "激光" in cat:
        return "关闭激光器，评估伤情并就医"
    if "电气" in cat:
        return "立即断电，必要时进行心肺复苏，拨打急救电话"
    if "危废" in cat:
        return "隔离泄漏区域，佩戴PPE处理，按危废应急预案上报"
    return "按实验室应急预案处理，必要时撤离并报警"


def build_source_info(entry):
    source = str(entry.get("source", "")).strip()
    batch = str(entry.get("data_source_batch", "")).strip()

    source_title = source
    if entry.get("standard_name"):
        source_title = entry.get("standard_name")
    elif entry.get("source_document"):
        source_title = entry.get("source_document")
    elif entry.get("reference") and isinstance(entry.get("reference"), str):
        source_title = entry.get("reference")

    source_type = "authoritative_manual"
    if batch == "标准文档":
        source_type = "regulatory_standard"
    elif batch == "高校手册SDS":
        source_type = "university_manual"
    elif batch == "培训制度通用":
        source_type = "制度"
    elif batch == "应急PPE":
        source_type = "应急预案"
    elif any(x in source for x in ["Cornell", "OSHA", "NIH", "CDC", "NRC", "EPA", "WHO"]):
        source_type = "public_authoritative_source"

    source_org = ""
    if "Cornell" in source:
        source_org = "Cornell University EHS"
    elif "OSHA" in source:
        source_org = "OSHA"
    elif "NIH" in source:
        source_org = "NIH"
    elif "CDC" in source:
        source_org = "CDC"
    elif "NRC" in source or "University of Toronto" in source:
        source_org = "NRC / University of Toronto"
    elif "ANSI" in source:
        source_org = "ANSI"
    elif "GB" in source or "国标" in source or "教育部" in source:
        source_org = "中国国家标准化管理委员会 / 教育部"
    elif "Sigma" in source or "Merck" in source:
        source_org = "Sigma-Aldrich / Merck"
    elif "清华大学" in source:
        source_org = "清华大学"
    elif "北京大学" in source:
        source_org = "北京大学"
    elif "浙江大学" in source:
        source_org = "浙江大学"
    elif "中山大学" in source:
        source_org = "中山大学"
    elif "武汉大学" in source:
        source_org = "武汉大学"
    elif "University of Guelph" in source:
        source_org = "University of Guelph"
    elif "Agilent" in source:
        source_org = "Agilent Technologies"
    elif "PerkinElmer" in source:
        source_org = "PerkinElmer"
    elif "EPA" in source:
        source_org = "EPA"
    elif "WHO" in source:
        source_org = "WHO"
    elif "IAEA" in source:
        source_org = "IAEA"
    elif "NFPA" in source:
        source_org = "NFPA"

    references = source
    if entry.get("regulatory_reference"):
        references = str(entry.get("regulatory_reference"))
    elif entry.get("reference") and isinstance(entry.get("reference"), str):
        references = entry.get("reference")
    elif entry.get("standard_code"):
        references = f"{entry.get('standard_code')} {entry.get('standard_name', '')}"

    return source_type, source_title, source_org, references


def is_duplicate(entry, existing_titles):
    title = str(entry.get("title", "")).strip()
    if title in existing_titles:
        return True, "exact_title"
    for et in existing_titles:
        if et and title and (et in title or title in et) and et != title:
            return True, f"fuzzy_match({et})"
    return False, ""


def convert_entry(entry):
    title = str(entry.get("title", "")).strip()
    raw_cat = str(entry.get("category", "")).strip()
    subcategory = str(entry.get("subcategory", "")).strip()

    category = CATEGORY_MAP.get(raw_cat, raw_cat)
    lab_type = LAB_TYPE_MAP.get(category, "通用")

    risk_text = ""
    for key in ["hazards", "safety_measures", "description", "content", "title"]:
        val = entry.get(key)
        if val:
            risk_text += " " + (" ".join(val) if isinstance(val, list) else str(val))
    risk_level = infer_risk_level(risk_text)

    hazards = entry.get("hazards")
    hazard_types = join_array(hazards, ";") if hazards else ""

    scenario = generate_scenario(title, category, subcategory)
    question = generate_question(title, category, subcategory)

    answer = build_answer(entry)
    steps = build_steps(entry)
    ppe = build_ppe(entry)
    forbidden = build_forbidden(entry)
    disposal = build_disposal(entry)
    first_aid = build_first_aid(entry)
    emergency = build_emergency(entry)

    legal_notes = "遵守相关法律法规和实验室安全管理制度"
    if entry.get("regulatory_reference"):
        legal_notes += "；参照" + str(entry.get("regulatory_reference"))

    source_type, source_title, source_org, references = build_source_info(entry)

    batch = str(entry.get("data_source_batch", "")).strip()
    tags = f"{batch};{raw_cat}"
    if subcategory:
        tags += f";{subcategory}"

    row = {
        "id": next_id(),
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "lab_type": lab_type,
        "risk_level": risk_level,
        "hazard_types": hazard_types,
        "scenario": scenario,
        "question": question,
        "answer": answer,
        "steps": steps,
        "ppe": ppe,
        "forbidden": forbidden,
        "disposal": disposal,
        "first_aid": first_aid,
        "emergency": emergency,
        "legal_notes": legal_notes,
        "references": references,
        "source_type": source_type,
        "source_title": source_title,
        "source_org": source_org,
        "source_version": "",
        "source_date": "",
        "source_url": "",
        "last_updated": TODAY,
        "reviewer": "auto-ingest; pending human review",
        "status": "draft",
        "tags": tags,
        "language": "zh-CN",
    }
    return row


def main():
    if not NEW_DATA_FILE.exists():
        print(f"ERROR: {NEW_DATA_FILE} not found")
        return 1

    existing_rows = []
    existing_titles = set()
    existing_sigs = set()
    max_kb_num = 0

    if KB_FILE.exists():
        with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
                t = row.get("title", "").strip()
                if t:
                    existing_titles.add(t)
                existing_sigs.add(sig(t, row.get("question", "").strip()))
                rid = row.get("id", "")
                m = re.match(r"KB-NEW-(\d+)", rid)
                if m:
                    max_kb_num = max(max_kb_num, int(m.group(1)))

    print(f"现有知识库条目: {len(existing_rows)}")
    print(f"现有唯一title数: {len(existing_titles)}")
    print(f"现有最大 KB-NEW ID: {max_kb_num}")

    global ID_SEQ
    ID_SEQ = max_kb_num

    with NEW_DATA_FILE.open("r", encoding="utf-8") as f:
        new_data = json.load(f)

    print(f"新数据总条目: {len(new_data)}")

    skipped = {"exact_title": 0, "fuzzy_match": 0}
    new_rows = []
    dup_details = []

    for entry in new_data:
        is_dup, reason = is_duplicate(entry, existing_titles)
        if is_dup:
            if reason.startswith("fuzzy"):
                skipped["fuzzy_match"] += 1
            else:
                skipped["exact_title"] += 1
            dup_details.append(f"跳过: {entry.get('title')} | 原因: {reason}")
            continue

        row = convert_entry(entry)
        s = sig(row["title"], row["question"])
        if s in existing_sigs:
            skipped["fuzzy_match"] += 1
            dup_details.append(f"跳过(签名重复): {entry.get('title')}")
            continue

        existing_sigs.add(s)
        existing_titles.add(row["title"])
        new_rows.append(row)

    print(f"\n去重结果:")
    print(f"  完全重复title跳过: {skipped['exact_title']}")
    print(f"  模糊匹配跳过: {skipped['fuzzy_match']}")
    print(f"  实际新增: {len(new_rows)}")

    if not new_rows:
        print("没有新条目需要添加。")
        return 0

    all_rows = existing_rows + new_rows
    with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in all_rows:
            clean = {h: row.get(h, "") for h in HEADERS}
            writer.writerow(clean)

    print(f"\n完成。知识库总条目: {len(all_rows)}")

    report_path = REPO_ROOT / "ingest_report.md"
    batch_stats = {}
    cat_stats = {}
    for row in new_rows:
        b = row.get("tags", "").split(";")[0]
        batch_stats[b] = batch_stats.get(b, 0) + 1
        cat_stats[c] = cat_stats.get(c, 0) + 1 if (c := row.get("category", "")) else 0

    with report_path.open("w", encoding="utf-8") as f:
        f.write("# 实验室安全数据整合报告\n\n")
        f.write(f"**整合时间**: {TODAY}\n\n")
        f.write("## 统计摘要\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 整合前知识库条目 | {len(existing_rows)} |\n")
        f.write(f"| 新数据总条目 | {len(new_data)} |\n")
        f.write(f"| 完全重复跳过 | {skipped['exact_title']} |\n")
        f.write(f"| 模糊匹配跳过 | {skipped['fuzzy_match']} |\n")
        f.write(f"| **实际新增** | **{len(new_rows)}** |\n")
        f.write(f"| 整合后知识库条目 | {len(all_rows)} |\n\n")

        f.write("## 按批次分布（新增）\n\n")
        f.write("| 批次 | 数量 |\n|------|------|\n")
        for k, v in sorted(batch_stats.items(), key=lambda x: -x[1]):
            f.write(f"| {k} | {v} |\n")
        f.write("\n")

        f.write("## 按分类分布（新增）\n\n")
        f.write("| 分类 | 数量 |\n|------|------|\n")
        for k, v in sorted(cat_stats.items(), key=lambda x: -x[1]):
            f.write(f"| {k} | {v} |\n")
        f.write("\n")

        f.write("## 去重详情\n\n")
        f.write("```\n")
        for d in dup_details:
            f.write(d + "\n")
        f.write("```\n")

    print(f"报告已生成: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
