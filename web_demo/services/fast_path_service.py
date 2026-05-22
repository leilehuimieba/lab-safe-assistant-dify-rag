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
    "配酸稀释": ["配酸", "稀释", "酸", "浓酸"],
    "离心机基础": ["离心机", "转子", "离心管"],
    "访客准入": ["访客", "参观", "儿童", "未成年人", "小朋友"],
    "安全培训准入": ["培训", "准入", "考核", "实验室"],
    "风险评估": ["风险评估", "风险识别", "控制措施", "评估"],
}


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
        if _parse_risk_level(row.get("risk_level", "")) >= 4:
            continue
        best_score = max((_score_row_for_domain(question, row, domain) for domain in domains), default=0.0)
        if used_history_domains and best_score > 0:
            best_score += 3.0
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
