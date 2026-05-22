from __future__ import annotations

import re
from typing import Any

from ..models import Citation
from ..repositories import get_kb_entries, normalize_search_text


FAST_PATH_KEYWORDS = [
    ("个人防护", ["个人防护", "ppe", "护目镜", "实验服", "手套", "口罩", "鞋", "穿戴", "封闭式鞋", "凉鞋", "拖鞋", "高跟鞋", "长裤"]),
    ("通风柜", ["通风柜", "排风柜", "风罩", "窗扇", "前窗", "面风速", "报警", "认证", "关闭通风柜"]),
    ("甲醛使用", ["甲醛", "福尔马林", "formaldehyde"]),
    ("二氯甲烷", ["二氯甲烷", "dcm", "ch2cl2", "methylene chloride", "卤代溶剂"]),
    ("过期化学品", ["过期化学品", "过期试剂", "过期药品", "过期危化品", "过期试剂瓶"]),
    ("重金属废液", ["重金属废液", "含重金属", "汞废液", "铅废液", "镉废液", "铬废液", "六价铬"]),
    ("实验室停电", ["停电", "断电", "突然停电", "实验室停电", "停电应急"]),
    ("马弗炉", ["马弗炉", "muffle furnace", "灰化", "焙烧", "高温炉", "坩埚"]),
    ("废弃物", ["废弃物", "废液", "废试剂", "废瓶", "试剂瓶", "空瓶", "危废", "废液桶", "垃圾分类"]),
    ("标签标识", ["标签", "标识", "标记", "名称", "浓度", "配制日期", "责任人", "标签缺失", "标签不完整", "废液标签"]),
    ("化学品储存", ["储存", "存放", "防火柜", "试剂柜", "安全柜", "乙醇", "易燃液体", "分类储存", "不相容", "氧化剂", "混放", "同一个柜子", "同柜", "硝酸"]),
    ("配酸稀释", ["配酸", "稀释浓酸", "浓酸稀释", "酸入水", "酸倒入水中", "把酸倒进水里", "先加水", "先加酸", "加酸到水里", "倒入水", "加酸"]),
    ("离心机基础", ["离心机", "平衡", "转头", "离心管", "盖子", "启动前", "低速", "异常振动", "震动", "振动", "抖动", "异响", "噪音", "停机", "停稳"]),
    ("访客准入", ["参观", "访客", "外来人员", "来访", "小朋友", "儿童", "未成年人", "带孩子", "带小孩"]),
    ("安全培训准入", ["培训", "准入", "第一课", "第一次进实验", "进实验前", "进入实验室前", "新进实验室", "安全内容", "考核", "第一次做实验前", "做实验前", "必须满足什么条件", "新同学", "开始实验前"]),
    ("风险评估", ["风险评估", "评估步骤", "基本步骤", "风险识别", "控制措施", "风险分析"]),
    ("基础应知", ["实验室前", "进入实验室", "注意事项", "基本要求", "实验室穿什么", "可以穿", "准入"]),
]

DOMAIN_REQUIRED_MARKERS = {
    "化学品储存": ["储存", "存放", "柜", "不相容", "氧化剂", "易燃", "硝酸", "乙醇"],
    "甲醛使用": ["甲醛", "福尔马林", "formaldehyde"],
    "二氯甲烷": ["二氯甲烷", "dcm", "ch2cl2", "卤代"],
    "过期化学品": ["过期", "危废", "处置", "过氧化物"],
    "重金属废液": ["重金属", "汞", "铅", "镉", "铬", "六价铬"],
    "实验室停电": ["停电", "断电", "应急", "关闭"],
    "马弗炉": ["马弗炉", "高温", "坩埚", "灰化", "焙烧"],
    "配酸稀释": ["配酸", "稀释", "酸", "浓酸"],
    "离心机基础": ["离心机", "转子", "离心管"],
    "访客准入": ["访客", "参观", "儿童", "未成年人", "小朋友"],
    "安全培训准入": ["培训", "准入", "考核", "实验室"],
    "风险评估": ["风险评估", "风险识别", "控制措施", "评估"],
}

FAST_PATH_HIGH_RISK_ALLOWED_DOMAINS = {"甲醛使用", "二氯甲烷", "重金属废液"}


def _match_domain(question: str, citation: Citation, row: dict[str, str] | None = None) -> str | None:
    q = normalize_search_text(question)
    title = normalize_search_text(citation.title)
    source = normalize_search_text(citation.source_title)
    tags = normalize_search_text(" ".join([
        (row or {}).get("tags", ""),
        (row or {}).get("category", ""),
        (row or {}).get("subcategory", ""),
        (row or {}).get("hazard_types", ""),
    ]))
    for domain, keywords in FAST_PATH_KEYWORDS:
        if any(keyword in q for keyword in keywords):
            if any(keyword in title or keyword in source or keyword in tags for keyword in keywords):
                return domain
    return None


def _question_domains(question: str) -> list[str]:
    q = normalize_search_text(question)
    domains = [
        domain
        for domain, keywords in FAST_PATH_KEYWORDS
        if any(keyword in q for keyword in keywords)
    ]
    if domains:
        return domains
    if any(token in q for token in ["实验室", "安全", "要求"]):
        return ["基础应知"]
    return []


def _history_domains(history: list[dict[str, str]] | None) -> list[str]:
    if not history:
        return []
    found: list[str] = []
    for item in history[-2:]:
        text = " ".join([
            str(item.get("question") or ""),
            str(item.get("answer") or ""),
        ])
        for domain in _question_domains(text):
            if domain not in found:
                found.append(domain)
    return found


def _allow_fast_path_with_history(question: str, history: list[dict[str, str]] | None, domains: list[str]) -> bool:
    q = normalize_search_text(question)
    if not domains:
        return False
    if any(token in q for token in ["起火", "着火", "泄漏", "冒烟", "灼伤", "受伤", "爆炸", "报警"]):
        return False
    if "离心机基础" in domains and any(token in q for token in ["震动", "振动", "抖动", "抖", "异响", "噪音", "停机", "停稳", "掀盖", "开盖"]):
        return True
    if any(token in q for token in ["怎么办", "怎么处理", "如何处理"]) and any(domain not in {"标签标识", "化学品储存", "废弃物"} for domain in domains):
        return False
    return bool(history)


def _row_matches_domain(row: dict[str, str], domain: str) -> bool:
    keywords = dict(FAST_PATH_KEYWORDS).get(domain, [])
    haystacks = [
        row.get("title_blob", ""),
        row.get("tag_blob", ""),
        row.get("body_blob", ""),
        normalize_search_text(row.get("question", "")),
    ]
    combined = " ".join(haystacks)
    required_markers = DOMAIN_REQUIRED_MARKERS.get(domain, [])
    if required_markers and not any(marker in combined for marker in required_markers):
        return False
    return any(keyword in haystack for keyword in keywords for haystack in haystacks)


def _parse_risk_level(value: str) -> int:
    try:
        return int(float(value or "0"))
    except ValueError:
        return 0


def _allow_row_by_risk(domain: str, risk_level: int) -> bool:
    if risk_level >= 5:
        return False
    if risk_level >= 4:
        return domain in FAST_PATH_HIGH_RISK_ALLOWED_DOMAINS
    return True


def _row_to_citation(row: dict[str, str], *, score: float) -> Citation:
    return Citation(
        kb_id=row.get("id", "").strip(),
        title=row.get("title", "").strip(),
        source_title=row.get("source_title", "").strip(),
        source_org=row.get("source_org", "").strip(),
        source_url=row.get("source_url", "").strip(),
        risk_level=row.get("risk_level", "").strip(),
        snippet=" ".join(
            item for item in [
                row.get("answer", "").strip(),
                row.get("steps", "").strip(),
                row.get("forbidden", "").strip(),
            ] if item
        )[:500],
        score=round(score, 2),
    )


def _score_row_for_domain(question: str, row: dict[str, str], domain: str) -> float:
    q = normalize_search_text(question)
    row_question = normalize_search_text(row.get("question", ""))
    title_blob = row.get("title_blob", "")
    tag_blob = row.get("tag_blob", "")
    body_blob = row.get("body_blob", "")
    keywords = dict(FAST_PATH_KEYWORDS).get(domain, [])

    if not _row_matches_domain(row, domain):
        return 0.0

    score = 2.0
    if row_question:
        if q == row_question:
            score += 12.0
        elif row_question in q:
            score += 8.0
        elif q in row_question:
            score += 7.0

    for keyword in keywords:
        if keyword not in q:
            continue
        if keyword in title_blob:
            score += 2.8
        if keyword in tag_blob:
            score += 2.2
        if keyword in body_blob:
            score += 1.4

    if any(token in q for token in ["怎么办", "怎么处理", "如何处理"]) and any(token in title_blob + body_blob for token in ["处理", "处置", "清洗", "移交"]):
        score += 1.5
    if any(token in q for token in ["要求", "需要", "必须", "注意"]) and any(token in title_blob + body_blob for token in ["要求", "必须", "注意", "规范"]):
        score += 1.2
    if any(token in q for token in ["检查", "启动前", "使用前"]) and any(token in title_blob + body_blob for token in ["检查", "启动前", "使用前", "确认"]):
        score += 1.5
    if any(token in q for token in ["震动", "振动", "抖动", "异响", "噪音"]) and any(token in title_blob + body_blob for token in ["震动", "振动", "抖动", "异响", "噪音", "停机", "停稳"]):
        score += 1.8
    if any(token in q for token in ["培训", "准入", "考核", "第一课", "进实验前"]) and any(token in title_blob + body_blob for token in ["培训", "准入", "考核", "上岗", "进入实验室"]):
        score += 1.8
    if any(token in q for token in ["风险评估", "评估步骤", "风险识别", "控制措施"]) and any(token in title_blob + body_blob for token in ["风险评估", "风险识别", "控制措施", "风险分析"]):
        score += 2.0
    if any(token in q for token in ["参观", "访客", "小朋友", "儿童", "未成年人"]) and any(token in title_blob + body_blob for token in ["参观", "访客", "儿童", "未成年人", "陪同", "登记"]):
        score += 1.8
    if any(token in q for token in ["配酸", "稀释浓酸", "酸入水", "先加水", "先加酸"]) and any(token in title_blob + body_blob for token in ["配酸", "稀释浓酸", "酸入水", "先加水", "先加酸"]):
        score += 1.8
    if any(token in q for token in ["同一个柜子", "同柜", "混放", "硝酸"]) and any(token in title_blob + body_blob for token in ["同柜", "混放", "不相容", "氧化剂", "硝酸", "易燃"]):
        score += 2.0
    if domain == "化学品储存" and any(token in row_question + title_blob for token in ["氧化剂", "不相容", "混放", "硝酸", "乙醇"]):
        score += 2.2
    if domain == "甲醛使用" and any(token in title_blob + body_blob for token in ["致癌", "孕", "生殖", "通风柜", "密闭"]):
        score += 3.0
    if domain == "二氯甲烷" and any(token in title_blob + body_blob for token in ["IARC", "2A", "卤代", "通风柜", "手套"]):
        score += 3.0
    if domain == "过期化学品" and any(token in title_blob + body_blob for token in ["过氧化物", "结晶", "爆炸", "专业处置"]):
        score += 3.0
    if domain == "重金属废液" and any(token in title_blob + body_blob for token in ["汞", "铅", "镉", "铬", "六价铬", "专桶"]):
        score += 3.0
    if domain == "实验室停电" and any(token in title_blob + body_blob for token in ["停电", "断电", "气瓶", "加热", "应急照明"]):
        score += 3.0
    if domain == "马弗炉" and any(token in title_blob + body_blob for token in ["坩埚", "预干燥", "开门", "高温", "通风"]):
        score += 3.0
    if domain == "离心机基础" and any(token in q for token in ["震动", "振动", "抖动", "异响", "噪音"]):
        if any(token in title_blob + body_blob for token in ["离心机", "振动", "转子", "停机", "开盖"]):
            score += 3.0
    if domain == "离心机基础" and "离心机" in row_question + title_blob:
        score += 1.6
    if domain == "安全培训准入" and any(token in q for token in ["培训", "准入", "第一课", "安全内容", "进实验前", "做实验前", "满足什么条件", "新同学"]):
        if any(token in title_blob + body_blob for token in ["培训", "准入", "考核", "SDS", "应急", "PPE"]):
            score += 2.6
    if domain == "安全培训准入" and any(token in row_question + title_blob for token in ["培训", "准入", "新进实验室", "进入实验室"]):
        score += 2.2
    if domain == "访客准入" and any(token in row_question + title_blob for token in ["参观", "访客", "儿童", "未成年人", "小朋友"]):
        score += 2.2
    if domain == "风险评估" and any(token in row_question + title_blob for token in ["风险评估", "风险识别", "控制措施", "生物安全风险评估"]):
        score += 2.4
    if domain == "配酸稀释" and any(token in q for token in ["稀释浓酸", "酸倒入水中", "倒入水", "加酸"]):
        if any(token in title_blob + body_blob for token in ["先加水", "加入酸", "酸入水", "配酸"]):
            score += 2.8
    if domain == "配酸稀释" and any(token in row_question + title_blob for token in ["配酸", "先加水", "先加酸", "浓酸"]):
        score += 2.5
    if domain == "化学品储存" and "硝酸" in q and "乙醇" in q:
        if any(token in title_blob + body_blob for token in ["氧化剂", "易燃", "不相容", "隔离", "同层"]):
            score += 3.0
    if "什么时候" in q and any(token in title_blob + body_blob for token in ["何时", "结束后", "用完", "离开"]):
        score += 1.0

    return score


def _lookup_kb_row(kb_id: str) -> dict[str, str] | None:
    for row in get_kb_entries():
        if row.get("id", "").strip() == kb_id.strip():
            return row
    return None


def _split_items(text: str) -> list[str]:
    value = (text or "").strip()
    if not value:
        return []
    parts = re.split(r"[;；\n]+", value)
    cleaned = [item.strip(" -—•·\t ") for item in parts if item.strip(" -—•·\t ")]
    return [
        item for item in cleaned
        if normalize_search_text(item) not in {"n/a", "na", "none", "无", "暂无"}
    ]


def _first_sentence(text: str) -> str:
    value = re.sub(r"\s+", " ", (text or "").strip())
    if not value:
        return ""
    value = re.sub(r"^[A-Za-z][A-Za-z0-9 _:/.-]{8,}\s*", "", value)
    for sep in ("。", "；", ";", "!", "！", "?", "？"):
        if sep in value:
            return value.split(sep, 1)[0].strip()
    return value[:80].strip()


def _contains_any(items: list[str], keywords: list[str]) -> bool:
    haystack = normalize_search_text(" ".join(items))
    return any(normalize_search_text(keyword) in haystack for keyword in keywords)


def should_use_fast_path(
    *,
    question: str,
    citations: list[Citation],
    low_confidence: bool,
    rule: dict[str, Any] | None,
    session_has_history: bool,
) -> bool:
    if session_has_history:
        return False
    if low_confidence:
        return False
    return bool(select_fast_path_citations(
        question=question,
        citations=citations,
        low_confidence=low_confidence,
        rule=rule,
        session_has_history=session_has_history,
    ))


def select_fast_path_citations(
    *,
    question: str,
    citations: list[Citation],
    low_confidence: bool,
    rule: dict[str, Any] | None,
    session_has_history: bool,
    history: list[dict[str, str]] | None = None,
) -> list[Citation]:
    if low_confidence:
        return []

    q = normalize_search_text(question)
    if "硝酸" in q and "乙醇" in q and any(token in q for token in ["同一个柜子", "同柜", "混放"]):
        return []

    direct_domains = _question_domains(question)
    domains = list(direct_domains)
    used_history_domains = False
    if not domains and session_has_history:
        domains = _history_domains(history)
        used_history_domains = bool(domains)
    if not domains:
        return []
    if session_has_history and not _allow_fast_path_with_history(question, history, domains):
        return []

    ranked: list[tuple[float, Citation]] = []
    seen_ids: set[str] = set()

    for citation in citations:
        row = _lookup_kb_row(citation.kb_id)
        if not row:
            continue
        allowed_scores = []
        for domain in domains:
            risk_level = _parse_risk_level(row.get("risk_level", ""))
            if not _allow_row_by_risk(domain, risk_level):
                continue
            allowed_scores.append(_score_row_for_domain(question, row, domain))
        best_score = max(allowed_scores, default=0.0)
        if used_history_domains and best_score > 0:
            best_score += 3.0
        if best_score >= 6.0 and citation.kb_id not in seen_ids:
            ranked.append((citation.score + best_score, citation))
            seen_ids.add(citation.kb_id)

    for row in get_kb_entries():
        row_id = row.get("id", "").strip()
        if not row_id or row_id in seen_ids:
            continue
        allowed_scores = []
        for domain in domains:
            risk_level = _parse_risk_level(row.get("risk_level", ""))
            if not _allow_row_by_risk(domain, risk_level):
                continue
            allowed_scores.append(_score_row_for_domain(question, row, domain))
        best_score = max(allowed_scores, default=0.0)
        if used_history_domains and best_score > 0:
            best_score += 3.0
        threshold = 5.4 if used_history_domains else 6.2
        if best_score >= threshold:
            ranked.append((best_score, _row_to_citation(row, score=best_score)))
            seen_ids.add(row_id)

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = [citation for _, citation in ranked[:3]]
    if selected and any(token in q for token in ["同一个柜子", "同柜", "混放"]):
        top_text = normalize_search_text(" ".join([
            selected[0].title,
            selected[0].source_title,
            selected[0].snippet,
        ]))
        if not any(token in top_text for token in ["不相容", "氧化剂", "混放", "隔离", "分开存放"]):
            return []
    return selected


def build_fast_path_answer(question: str, citations: list[Citation]) -> str:
    top = citations[0]
    row = _lookup_kb_row(top.kb_id)
    domain = _match_domain(question, top, row) or "基础应知"
    q = normalize_search_text(question)
    context_text = normalize_search_text(
        " ".join(
            [
                question,
                top.title,
                top.source_title,
                (row or {}).get("question", ""),
                (row or {}).get("answer", ""),
                (row or {}).get("steps", ""),
            ]
        )
    )

    answer = (row or {}).get("answer", "").strip()
    steps = _split_items((row or {}).get("steps", ""))
    forbidden = _split_items((row or {}).get("forbidden", ""))
    ppe = _split_items((row or {}).get("ppe", ""))
    emergency = _split_items((row or {}).get("emergency", ""))

    summary = _first_sentence(answer) or _first_sentence(top.snippet)
    if not summary:
        summary = "请按实验室基础安全要求完成个人防护、环境核对并遵循书面 SOP。"

    if domain == "甲醛使用" and not any(token in summary for token in ["致癌", "孕", "生殖"]):
        summary = "甲醛具有刺激性并被列为致癌风险化学品，必须尽量降低吸入和皮肤暴露，孕期或计划怀孕人员应避免接触。"
    elif domain == "二氯甲烷" and not any(token in summary.lower() for token in ["iarc", "2a", "卤代"]):
        summary = "二氯甲烷挥发性强，通常按卤代有机溶剂管理，存在致癌风险，必须在通风柜内操作并严格控暴露。"
    elif domain == "过期化学品" and "过氧化物" not in summary:
        summary = "过期化学品一律按危废管理，其中乙醚、THF 等过氧化物形成物要特别警惕结晶、爆炸和禁止随意开盖移动。"
    elif domain == "重金属废液" and not any(token in summary for token in ["汞", "铅", "镉", "铬"]):
        summary = "含重金属废液必须专桶、专标识、专暂存，严禁下水道，汞、铅、镉、六价铬等应作为重点污染物单独管理。"
    elif domain == "实验室停电" and not any(token in summary for token in ["气瓶", "加热", "照明"]):
        summary = "实验室停电时要先控风险源，再保人员与关键设备安全，重点是关闭加热设备、气源并确认通风与应急照明状态。"
    elif domain == "马弗炉" and not any(token in summary for token in ["坩埚", "预干燥", "开门"]):
        summary = "马弗炉属于高温高风险设备，样品类型、坩埚材质、隔热手套和安全开门温度都必须符合要求。"
    elif domain == "个人防护" and not any(token in summary for token in ["PPE", "封闭鞋"]):
        summary = "化学实验的基础 PPE 通常包括护目镜、实验服、合适手套和封闭鞋，必要时再升级面罩、围裙或呼吸防护。"

    if not steps:
        if domain == "标签标识":
            steps = [
                "核对化学品名称、浓度和危险性信息",
                "补充配制日期、责任人等追溯信息",
                "发现标签不清或缺失时暂停使用并立即补贴",
            ]
        elif domain == "化学品储存":
            steps = [
                "确认容器密封完好并贴有清晰标签",
                "按危险特性分类放入对应试剂柜或防火柜",
                "保持远离热源、火源和不相容化学品",
            ]
        elif domain == "甲醛使用":
            steps = [
                "全程在通风柜内操作，确认前窗高度、风速报警和容器密闭状态正常",
                "佩戴护目镜、实验服和合适防化手套，避免吸入蒸气和皮肤接触",
                "孕期或计划怀孕人员应先做岗位暴露评估，废液按危废分类收集并清晰标识",
            ]
        elif domain == "二氯甲烷":
            steps = [
                "所有开盖、转移和萃取操作都在通风柜内完成，避免在柜外短时暴露",
                "优先选用对卤代溶剂更合适的手套方案，长时间接触不要只依赖普通薄丁腈手套",
                "废液收入卤代有机废液桶，不与非卤代有机废液混装",
            ]
        elif domain == "过期化学品":
            steps = [
                "先核对标签、开封日期和危险类别，按危废分类密闭、贴签和登记台账",
                "对乙醚、THF、二恶烷等可能形成过氧化物的试剂，发现瓶口结晶或可疑沉积时不要再开盖移动",
                "联系有资质的危废处置单位或校内危化管理员统一评估和移交",
            ]
        elif domain == "重金属废液":
            steps = [
                "将含汞、铅、镉、铬、六价铬等废液专桶收集，避免与有机废液、酸碱废液混装",
                "容器标注“重金属废液”以及主要成分、浓度、日期和责任人，保持密封暂存",
                "按危废流程交由有资质单位清运处置，严禁排入下水道",
            ]
        elif domain == "实验室停电":
            steps = [
                "先停止实验并关闭电热套、加热板、搅拌器等带热源设备，防止来电后自启动",
                "能安全做到时关闭气瓶总阀和相关工艺阀门，确认通风柜、低温冰箱和培养箱等关键设备状态",
                "启用应急照明并报告负责人/物业，待供电恢复后按 SOP 逐项复机",
            ]
        elif domain == "马弗炉":
            steps = [
                "样品进炉前先确认无残留溶剂、非密闭、非未知成分，并选用陶瓷/石英/铂等合适坩埚",
                "按程序升温，取样或开门时站在炉门侧面，先开一条缝降温散气，再用长柄坩埚钳操作",
                "高温坩埚放在耐热垫上冷却，设备周围保持无可燃物并保证排风良好",
            ]
        elif domain == "配酸稀释":
            steps = [
                "先在耐热容器中加入水，必要时先做冰浴降温",
                "将浓酸沿器壁缓慢加入水中并持续搅拌",
                "全程佩戴护目镜、实验服和合适手套，严禁反向加料",
            ]
        elif domain == "离心机基础":
            steps = [
                "检查离心管配平、转头状态和盖子锁定",
                "确认参数设置与样品耐受范围一致",
                "异常振动或噪音时立即停机检查",
            ]
        elif domain == "访客准入":
            steps = [
                "先确认该实验室是否允许访客或未成年人进入",
                "安排教师或实验室负责人全程陪同并完成安全告知",
                "按要求提供 PPE、限制接触设备和化学品，并做好登记",
            ]
        elif domain == "安全培训准入":
            steps = [
                "先完成实验室通用安全培训和准入考核",
                "再完成课题组现场风险告知与设备专项培训",
                "确认熟悉应急路线、PPE 和化学品标签/SDS 后再进入",
            ]
        elif domain == "风险评估":
            steps = [
                "先识别实验中涉及的人员、化学品、设备和环境风险",
                "再评估风险等级、暴露途径和最坏后果",
                "最后落实控制措施、应急方案并在操作前复核",
            ]
        elif domain == "通风柜":
            steps = [
                "检查风速和报警状态是否正常",
                "前窗保持在安全刻度以内",
                "仅在柜内完成挥发性或刺激性操作，结束后延时关闭",
            ]
        elif domain == "废弃物":
            steps = [
                "先判断废弃物类别并选择对应容器",
                "分类收集并保持标签清晰",
                "按危废流程暂存和移交，不得随意倾倒",
            ]
        elif domain == "个人防护":
            steps = [
                "进入实验区前确认实验服、护目镜和手套是否符合要求",
                "脚部与下肢保持封闭防护，避免露趾、露腿或易卷入着装",
                "现场风险变化时按 SOP 升级防护级别",
            ]
        else:
            steps = [
                "先按实验室基础安全要求完成个人防护与环境检查",
                "再对照对应设备或化学品的书面 SOP 执行",
                "如现场条件与常规流程不一致，先暂停并询问老师或安全员",
            ]

    if domain == "甲醛使用":
        steps = [
            "全程在通风柜内操作，确认前窗高度、风速报警和容器密闭状态正常",
            "佩戴护目镜、实验服和合适防化手套，避免吸入蒸气和皮肤接触",
            "孕妇或计划怀孕人员应先做岗位暴露评估，废液按危废分类收集并清晰标识",
        ]
    elif domain == "二氯甲烷":
        steps = [
            "所有开盖、转移和萃取操作都在通风柜内完成，避免在柜外短时暴露",
            "优先选用对卤代溶剂更合适的手套方案，长时间接触不要只依赖普通薄丁腈手套",
            "废液收入卤代废液桶或卤代有机废液桶，不与非卤代有机废液混装",
        ]
    elif domain == "过期化学品":
        steps = [
            "先核对标签、开封日期和危险类别，按危废分类密闭、贴签和登记台账",
            "对乙醚、THF、二恶烷等可能形成过氧化物的试剂，发现瓶口结晶或可疑沉积时不要再开盖移动",
            "联系有资质的危废处置单位或校内危化管理员统一评估、专业处置和移交",
        ]
    elif domain == "重金属废液":
        steps = [
            "将含汞、铅、镉、铬、六价铬等废液单独收集、专桶暂存，避免与有机废液、酸碱废液混装",
            "容器标注“重金属废液”以及主要成分、浓度、日期和责任人，保持密封暂存",
            "按危废流程交由有资质单位专业处置，严禁排入下水道",
        ]
    elif domain == "实验室停电" and not _contains_any(steps, ["加热", "气瓶", "应急照明", "复机"]):
        steps = [
            "先停止实验并关闭电热套、加热板、搅拌器等带热源设备，防止来电后自启动",
            "能安全做到时关闭气瓶阀门和相关工艺阀门，确认通风柜、低温冰箱和培养箱等关键设备状态",
            "启用应急照明并报告负责人/物业，待供电恢复后按 SOP 逐项复机",
        ]
    elif domain == "马弗炉" and not _contains_any(steps, ["坩埚", "预干燥", "开门", "长柄", "耐热"]):
        steps = [
            "样品进炉前先确认无残留溶剂、非密闭、非未知成分，并选用陶瓷/石英/铂等合适坩埚",
            "按程序升温，佩戴隔热手套，取样或开门时站在炉门侧面，达到安全开门温度后先开一条缝散气，再用长柄坩埚钳操作",
            "高温坩埚放在耐热垫上冷却，设备周围保持无可燃物并保证排风良好",
        ]
    elif domain == "个人防护" and not _contains_any(steps, ["PPE", "封闭鞋", "护目镜"]):
        steps = [
            "先按实验内容确认 PPE：护目镜、实验服、合适手套是化学实验基础配置",
            "脚部穿封闭鞋，避免凉鞋、拖鞋、露趾鞋或高跟鞋进入实验区",
            "遇强腐蚀、飞溅、粉尘或挥发性风险时，再按 SOP 升级面罩、围裙或呼吸防护",
        ]

    if "防火柜" in q:
        summary = "防火柜用于规范暂存易燃液体，重点是分类入柜、柜门关闭、远离氧化剂，并保持接地或通风要求符合制度。"
        steps = [
            "按危险特性分类入柜，易燃液体与强氧化剂、强酸等不相容化学品分开存放",
            "取放后及时关闭柜门，控制柜内暂存量，不把防火柜当普通杂物柜使用",
            "按本单位要求落实接地、通风和定期检查，柜内容器保持密闭和清晰标签",
        ]
        forbidden = [
            "把氧化剂、强腐蚀品或无标签容器混放进防火柜",
            "柜门长期敞开、超量堆放或把纸箱杂物塞入柜内",
            "忽视接地/通风/巡检要求后继续长期使用",
        ]
    elif any(token in q for token in ["空试剂瓶", "空化学试剂瓶"]):
        summary = "空试剂瓶不能按普通垃圾直接丢弃，必须先处理残液和标签，再按材质或危废要求分类回收。"
        steps = [
            "先倒空残液，残液和第一次清洗液按对应化学废液收入废液桶",
            "确认瓶内不再有明显危险残留后，去除或涂盖原危险标签，避免被误用",
            "再按学校制度做分类回收；若仍受污染或不确定，按危废容器处理",
        ]
        forbidden = [
            "带残液直接丢入普通垃圾",
            "未处理原标签就流入普通回收",
            "把清洗液直接倒入下水道",
        ]
    elif "封闭式鞋" in q or "封闭鞋" in q:
        summary = "实验室鞋类要求以封闭、防滑、稳固为核心；凉鞋、拖鞋、露趾鞋和高跟鞋都不适合进入实验区。"
        steps = [
            "穿包裹脚趾和脚背的封闭鞋，鞋底应防滑、稳固，避免吸水后打滑",
            "禁止凉鞋、拖鞋、露趾鞋、洞洞鞋和高跟鞋进入实验区",
            "高风险场景可按 SOP 升级为防砸、防穿刺或耐化学腐蚀安全鞋",
        ]
        forbidden = [
            "穿凉鞋、拖鞋、露趾鞋或高跟鞋做实验",
            "把普通布鞋当作高风险区域的唯一防护",
            "鞋面被污染后继续长时间使用不处理",
        ]
    elif "通风柜" in q and any(token in q for token in ["窗扇", "开到多高", "前窗"]):
        summary = "通风柜窗扇应保持在本柜体规定的安全高度，不要把头伸入柜内，报警或气流异常时必须停用。"
        steps = [
            "按柜体安全标线或规定高度操作，通常保持在指定安全高度范围内",
            "操作时手在柜内、头不伸入柜内，避免堆物堵塞进排风气流",
            "如风速报警、排风异常或窗扇损坏，应立即停用并报修",
        ]
        forbidden = [
            "把窗扇开得过高仍继续做挥发性操作",
            "将头部长时间伸入柜内观察或操作",
            "报警状态下继续使用或把通风柜当储物柜堆满物品",
        ]
    elif ("废液桶" in q and "标签" in q) or ("标签" in q and "废液桶" in q):
        summary = "废液桶标签至少要写清名称或主要成分、危险性、日期和责任人，确保后续暂存、转运和处置可追溯。"
        steps = [
            "标明废液名称或主要成分，混合废液要写出关键成分而不是只写“废液”",
            "补充危险性信息，如易燃、腐蚀、有毒、含卤代或含重金属等",
            "写明开始收集日期和责任人，标签保持清晰、耐污、可追溯",
        ]
        forbidden = [
            "只写“废液”而不写成分",
            "无日期、无责任人就长期暂存",
            "标签模糊脱落后仍继续往桶内加废液",
        ]
    elif any(token in q for token in ["第一天", "第一次做实验前", "新同学第一次", "必须满足什么条件"]):
        summary = "新同学第一次进入实验或独立操作前，必须先完成准入培训、PPE 要求、SOP 学习和导师确认。"
        steps = [
            "先完成实验室通用准入培训，认识 PPE、应急设施、危险标识和基本禁令",
            "学习本课题相关 SOP、化学品 SDS 和设备专项要求，经老师或导师确认理解后再上手",
            "完成必要考核或授权登记，确认具备进入实验区和开展操作的准入资格",
        ]
        forbidden = [
            "未培训、未考核就直接做实验",
            "不了解 SOP 和应急路线就独立上机或接触化学品",
            "把第一次进实验室当普通参观而省略准入授权",
        ]
    elif "风险评估" in q:
        summary = "实验室风险评估的基本步骤通常是：识别危害、评估风险、制定控制措施，并在条件变化后复审。"
        steps = [
            "先识别人员、化学品、设备、环境和操作步骤中的主要危害",
            "再评估暴露概率与后果严重性，判断风险等级和关键失效点",
            "据此制定控制措施与应急准备，并在实验前和条件变化后复审更新",
        ]
        forbidden = [
            "未识别危害就直接开展高风险实验",
            "只写一个“低风险”结论而没有控制措施",
            "实验条件已变更却继续沿用旧评估",
        ]
    elif any(token in q for token in ["酸倒入水", "酸入水", "稀释浓硫酸"]):
        summary = "稀释浓酸必须酸入水，核心原因是强放热会导致局部暴沸和飞溅；正确做法是慢慢加、做好 PPE 并优先在通风柜或通风良好处操作。"
        steps = [
            "先在耐热容器中加水，必要时提前冰浴降温，再沿器壁慢慢加入浓酸并持续搅拌",
            "全过程佩戴护目镜、实验服和合适手套，控制加料速度，防止强放热引发飞溅",
            "优先在通风柜或通风良好处进行，配制完成后及时贴签并检查容器温升",
        ]
        forbidden = [
            "把水直接倒入浓酸",
            "一次性快速倒入造成暴沸飞溅",
            "不戴 PPE 就在台面随意配酸",
        ]
    elif any(token in q for token in ["标签完全没", "不明液体", "标签没了"]):
        summary = "标签完全缺失的不明液体不得继续使用或擅自倾倒，必须按未知化学品先隔离、再上报、再由管理人员处置。"
        steps = [
            "立即停止使用并把容器单独隔离，避免与其他化学品混放或继续开盖转移",
            "不要凭气味、颜色或个人经验判断成分，更不要擅自倒掉或混入废液桶",
            "尽快报告实验室负责人或危化管理员，由有权限人员按未知化学品流程处理",
        ]
        forbidden = [
            "继续使用不明液体做实验",
            "自行闻气味、试反应来猜成分",
            "未报告就擅自处置或下水道排放",
        ]
    elif any(token in q for token in ["小朋友", "未成年人", "参观"]):
        summary = "实验室通常不允许无关访客尤其儿童随意进入；确需参观时应经过准入审批，并由授权人员全程陪同。"
        steps = [
            "先确认实验室是否允许访客或未成年人进入，并完成必要审批或登记",
            "安排有权限人员全程陪同，提前做安全告知，限制其接触化学品和设备",
            "根据区域风险决定是否仅在低风险区域短时参观，并提供必要防护",
        ]
        forbidden = [
            "未经审批就带儿童进入实验区",
            "让访客无人陪同接触设备、样品或化学品",
            "把高风险实验区当作普通开放参观场所",
        ]
    elif any(token in q for token in ["开封后", "开封日期", "多久检查一次标签"]):
        summary = "化学品开封后应立即补记开封日期和责任信息，并在每次使用前检查标签是否完整、清晰、可追溯。"
        steps = [
            "开封当天就补记开封日期、责任人和必要的有效期/复查要求",
            "每次使用前检查标签是否完整、清晰、未被污染或脱落，发现模糊应先补标",
            "对易形成过氧化物、易变质或受控化学品，按制度增加定期复核频率",
        ]
        forbidden = [
            "开封后长期不补记日期",
            "标签模糊仍继续使用",
            "把补标工作拖到化学品快用完才处理",
        ]
    elif any(token in q for token in ["标签模糊", "还能继续用吗", "还能不能继续用"]):
        summary = "标签模糊的化学品原则上不能继续使用，必须先确认身份并补标；在未确认前应按不明化学品保守处理。"
        steps = [
            "立即暂停使用，先根据台账、配制记录或同批次容器确认化学品身份",
            "确认无误后及时补全标签；若无法确认，应单独隔离并报告管理人员处理",
            "在补标完成前，不得继续分装、转移、混用或做实验",
        ]
        forbidden = [
            "凭记忆直接继续使用标签模糊化学品",
            "未确认成分就转移、混合或倒入废液桶",
            "把模糊标签问题拖着不处理",
        ]
    elif "离心机" in context_text and any(token in q for token in ["启动前", "检查什么", "必查项", "检查哪些"]):
        summary = "离心机启动前至少要检查配平、转头/盖锁、参数设置和异常停机条件，避免运转中振动、甩管或开盖事故。"
        steps = [
            "检查离心管是否配平、装载是否对称，样品和转速是否在转头允许范围内",
            "确认转头、盖锁和离心管状态完好，参数设置正确，防止转头/盖锁失效",
            "明确异常振动、异响或漏液时要立即停机，不得带故障继续运行",
        ]
        forbidden = [
            "未配平就启动",
            "盖锁未确认就直接加速",
            "发现异常振动仍硬撑着继续离心",
        ]
    elif "离心机" in context_text and any(token in q for token in ["震动", "振动", "抖", "抖动", "异响", "噪音"]):
        summary = "离心机一旦出现异常震动或异响，应立即停机，禁止继续运行，然后重点检查配平、转头和离心管状态。"
        steps = [
            "立即停机，等待设备完全停稳后再开盖检查，禁止继续强行运行",
            "优先复核样品是否配平、离心管是否破损、转头是否安装到位或老化",
            "排除故障并确认设备安全前，不得重新启动；必要时联系管理员或维修人员",
        ]
        forbidden = [
            "边震动边继续离心",
            "未停稳就开盖查看",
            "只重启不排查配平和转头问题",
        ]
    elif any(token in q for token in ["更新了危废标签模板", "新模板回答", "最新制度"]):
        summary = "如果学校已经发布新的危废标签模板，系统口径应以最新制度为准，知识库版本也要及时同步，必要时人工复核。"
        steps = [
            "优先按学校最新制度、最新版模板和最新发文要求回答，而不是沿用旧版本习惯说法",
            "同步更新知识库条目、模板字段和版本标识，避免前端答案与现行制度脱节",
            "当系统答案与最新制度不一致或用户场景特殊时，应提示人工复核或管理员确认",
        ]
        forbidden = [
            "明知制度更新仍继续按旧模板回答",
            "知识库版本不同步却宣称答案一定最新",
            "遇到制度冲突时不提示人工复核",
        ]

    if ppe and any(token in normalize_search_text(question) for token in ["个人防护", "ppe", "护目镜", "实验服", "手套", "口罩", "鞋"]):
        steps = [f"优先确认防护要求：{'、'.join(ppe[:4])}"] + steps[:2]

    if not forbidden:
        if domain == "标签标识":
            forbidden = [
                "无标签存放",
                "标签内容模糊仍继续使用",
                "未完成补标就转移或分装化学品",
            ]
        elif domain == "化学品储存":
            forbidden = [
                "与不相容化学品混放",
                "靠近热源、火源或阳光直晒",
                "超量暂存或长期放在实验台面",
            ]
        elif domain == "甲醛使用":
            forbidden = [
                "在通风柜外长时间开盖、转移或配制甲醛溶液",
                "忽视甲醛致癌/致敏风险而仅按普通刺激性试剂处理",
                "将甲醛废液倒入下水道或与普通生活垃圾混放",
            ]
        elif domain == "二氯甲烷":
            forbidden = [
                "在通风柜外使用或闻气味判断暴露是否严重",
                "长期接触时只依赖普通薄丁腈手套而不更换/升级防护",
                "把二氯甲烷废液混入非卤代有机废液桶",
            ]
        elif domain == "过期化学品":
            forbidden = [
                "把过期化学品直接倒入下水道或普通垃圾桶",
                "对可形成过氧化物的旧试剂强行开盖、蒸馏或搬动",
                "未登记、未评估危险性就私自转移或继续使用",
            ]
        elif domain == "重金属废液":
            forbidden = [
                "把含汞、铅、镉、铬等废液倒入下水道",
                "与有机废液或酸碱废液混装导致后续处置困难",
                "无标签暂存或使用不耐腐蚀容器长期存放",
            ]
        elif domain == "实验室停电":
            forbidden = [
                "停电后放任加热设备、反应装置和气源处于原状态",
                "在照明不足、通风异常时继续进行高风险实验",
                "未确认设备复位和环境安全就直接恢复运行",
            ]
        elif domain == "马弗炉":
            forbidden = [
                "将含溶剂、密闭、未知或可能爆炸的样品放入马弗炉",
                "高温时正对炉口猛开门或徒手取放坩埚",
                "把马弗炉放在可燃台面附近或排风不良处长期运行",
            ]
        elif domain == "配酸稀释":
            forbidden = [
                "把水直接倒入浓酸",
                "不降温就快速加料或剧烈摇晃",
                "未佩戴护目镜、实验服和手套就配酸",
            ]
        elif domain == "离心机基础":
            forbidden = [
                "未配平直接启动",
                "运转过程中强行开盖",
                "发现异常振动仍继续运行",
            ]
        elif domain == "访客准入":
            forbidden = [
                "让儿童或未成年人自行进入高风险实验室",
                "未告知风险、未陪同就让访客接触设备或化学品",
                "未登记或未提供必要防护就带人进入实验区",
            ]
        elif domain == "安全培训准入":
            forbidden = [
                "未培训、未考核就直接进入实验区操作",
                "未读 SDS、SOP 就接触化学品或设备",
                "把第一次进实验室当作普通参观而省略准入流程",
            ]
        elif domain == "风险评估":
            forbidden = [
                "未识别风险就直接开做高危实验",
                "只写结论不落实控制措施和应急准备",
                "现场条件变化后仍沿用旧评估不复核",
            ]
        elif domain == "通风柜":
            forbidden = [
                "报警状态下继续操作",
                "将头部伸入柜内或堵塞气流",
                "长期把通风柜当储物柜使用",
            ]
        elif domain == "废弃物":
            forbidden = [
                "倒入下水道或普通垃圾桶",
                "不同类别危废混装",
                "未贴标签就暂存或移交",
            ]
        elif domain == "个人防护":
            forbidden = [
                "穿凉鞋、拖鞋、高跟鞋或露趾鞋进入实验区",
                "高风险操作时省略护目镜、实验服或合适手套",
                "被化学品污染后继续穿戴不处理",
            ]
        else:
            forbidden = [
                "省略 PPE、通风、标签核对等基础步骤",
                "未确认兼容性前混放、混用或随意处置化学品/废弃物",
            ]

    if domain == "甲醛使用":
        forbidden = [
            "在通风柜外长时间开盖、转移或配制甲醛溶液",
            "忽视甲醛致癌/致敏风险而仅按普通刺激性试剂处理",
            "将甲醛废液倒入下水道或与普通生活垃圾混放",
        ]
    elif domain == "二氯甲烷":
        forbidden = [
            "在通风柜外使用或闻气味判断暴露是否严重",
            "长期接触时只依赖普通薄丁腈手套而不更换/升级防护",
            "把二氯甲烷废液混入非卤代有机废液桶",
        ]
    elif domain == "过期化学品":
        forbidden = [
            "把过期化学品直接倒入下水道或普通垃圾桶",
            "对可形成过氧化物的旧试剂强行开盖、蒸馏或搬动",
            "未登记、未评估危险性就私自转移或继续使用",
        ]
    elif domain == "重金属废液":
        forbidden = [
            "把含汞、铅、镉、铬等废液倒入下水道",
            "与有机废液或酸碱废液混装导致后续处置困难",
            "无标签暂存或使用不耐腐蚀容器长期存放",
        ]
    elif domain == "实验室停电" and not _contains_any(forbidden, ["加热", "气源", "恢复运行"]):
        forbidden = [
            "停电后放任加热设备、反应装置和气源处于原状态",
            "在照明不足、通风异常时继续进行高风险实验",
            "未确认设备复位和环境安全就直接恢复运行",
        ]
    elif domain == "马弗炉" and not _contains_any(forbidden, ["坩埚", "爆炸", "炉口", "排风"]):
        forbidden = [
            "将含溶剂、密闭、未知或可能爆炸的样品放入马弗炉",
            "高温时正对炉口猛开门或徒手取放坩埚",
            "把马弗炉放在可燃台面附近或排风不良处长期运行",
        ]

    forbidden_lines = [
        f"- 禁止{item}" if not item.startswith("禁止") else f"- {item}"
        for item in forbidden[:3]
    ]

    emergency_block = ""
    if emergency:
        emergency_block = "\n\n应急提醒:\n" + "\n".join(f"- {item}" for item in emergency[:2])

    return (
        "结论:\n"
        f"{summary}。\n\n"
        "步骤:\n"
        + "\n".join(f"{idx}. {item}" for idx, item in enumerate(steps[:3], start=1))
        + "\n\n禁止事项:\n"
        + "\n".join(forbidden_lines)
        + emergency_block
        + "\n\n参考依据:\n"
        f"- {top.kb_id}: {top.source_title or top.title}\n"
        f"- 相关命中 {min(len(citations), 3)} 条，可展开引用查看原始依据。"
    )
