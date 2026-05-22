from __future__ import annotations

import re
from typing import Any

from ..models import Citation
from ..repositories import get_kb_entries, normalize_search_text


FAST_PATH_KEYWORDS = [
    ("个人防护", ["个人防护", "ppe", "护目镜", "实验服", "手套", "口罩", "鞋", "穿戴", "封闭式鞋", "凉鞋", "拖鞋", "高跟鞋", "长裤"]),
    ("通风柜", ["通风柜", "排风柜", "风罩", "窗扇", "前窗", "面风速", "报警", "认证", "关闭通风柜"]),
    ("废弃物", ["废弃物", "废液", "废试剂", "废瓶", "试剂瓶", "空瓶", "危废", "废液桶", "垃圾分类"]),
    ("标签标识", ["标签", "标识", "标记", "名称", "浓度", "配制日期", "责任人", "标签缺失", "标签不完整", "废液标签"]),
    ("化学品储存", ["储存", "存放", "防火柜", "试剂柜", "安全柜", "乙醇", "易燃液体", "分类储存", "不相容", "氧化剂"]),
    ("离心机基础", ["离心机", "平衡", "转头", "离心管", "盖子", "启动前", "低速", "异常振动", "停稳"]),
    ("基础应知", ["实验室前", "进入实验室", "注意事项", "基本要求", "实验室穿什么", "可以穿", "准入"]),
]


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


def _row_matches_domain(row: dict[str, str], domain: str) -> bool:
    keywords = dict(FAST_PATH_KEYWORDS).get(domain, [])
    haystacks = [
        row.get("title_blob", ""),
        row.get("tag_blob", ""),
        row.get("body_blob", ""),
        normalize_search_text(row.get("question", "")),
    ]
    return any(keyword in haystack for keyword in keywords for haystack in haystacks)


def _parse_risk_level(value: str) -> int:
    try:
        return int(float(value or "0"))
    except ValueError:
        return 0


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
) -> list[Citation]:
    if session_has_history or low_confidence:
        return []

    domains = _question_domains(question)
    if not domains:
        return []

    ranked: list[tuple[float, Citation]] = []
    seen_ids: set[str] = set()

    for citation in citations:
        row = _lookup_kb_row(citation.kb_id)
        if not row:
            continue
        if _parse_risk_level(row.get("risk_level", "")) >= 4:
            continue
        best_score = max((_score_row_for_domain(question, row, domain) for domain in domains), default=0.0)
        if best_score >= 6.0 and citation.kb_id not in seen_ids:
            ranked.append((citation.score + best_score, citation))
            seen_ids.add(citation.kb_id)

    for row in get_kb_entries():
        row_id = row.get("id", "").strip()
        if not row_id or row_id in seen_ids:
            continue
        if _parse_risk_level(row.get("risk_level", "")) >= 4:
            continue
        best_score = max((_score_row_for_domain(question, row, domain) for domain in domains), default=0.0)
        if best_score >= 7.2:
            ranked.append((best_score, _row_to_citation(row, score=best_score)))
            seen_ids.add(row_id)

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [citation for _, citation in ranked[:3]]


def build_fast_path_answer(question: str, citations: list[Citation]) -> str:
    top = citations[0]
    row = _lookup_kb_row(top.kb_id)
    domain = _match_domain(question, top, row) or "基础应知"

    answer = (row or {}).get("answer", "").strip()
    steps = _split_items((row or {}).get("steps", ""))
    forbidden = _split_items((row or {}).get("forbidden", ""))
    ppe = _split_items((row or {}).get("ppe", ""))
    emergency = _split_items((row or {}).get("emergency", ""))

    summary = _first_sentence(answer) or _first_sentence(top.snippet)
    if not summary:
        summary = "请按实验室基础安全要求完成个人防护、环境核对并遵循书面 SOP。"

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
        elif domain == "离心机基础":
            steps = [
                "检查离心管配平、转头状态和盖子锁定",
                "确认参数设置与样品耐受范围一致",
                "异常振动或噪音时立即停机检查",
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
        elif domain == "离心机基础":
            forbidden = [
                "未配平直接启动",
                "运转过程中强行开盖",
                "发现异常振动仍继续运行",
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
