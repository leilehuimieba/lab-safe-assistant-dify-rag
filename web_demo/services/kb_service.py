from __future__ import annotations

"""知识库检索与规则匹配服务

- retrieve_citations: 基于 token 匹配 + 语义检索（bge-m3）混合打分检索 KB 条目
- match_rule: 按 severity、命中数和规则顺序匹配安全规则
- should_enforce_terminal_rule: 判断是否触发终止动作（refuse / redirect_emergency / ask_for_more_info / direct_safe_answer）
"""

import logging
import os
from typing import Any

from ..models import Citation
from ..repositories import (
    DEFAULT_TOP_K,
    SEVERITY_SCORE,
    TERMINAL_ACTIONS,
    REFUSE_INTENT_MARKERS,
    EMERGENCY_INTENT_MARKERS,
    has_casualty_report,
    normalize_search_text,
    extract_tokens,
    get_kb_entries,
    get_rules_config,
    KB_FILE,
)

logger = logging.getLogger(__name__)

# 语义检索可选依赖：未安装时自动 fallback 到纯文本检索
try:
    from libs.embedding_utils import semantic_search

    _EMBEDDING_AVAILABLE = True
except ImportError:  # pragma: no cover
    _EMBEDDING_AVAILABLE = False

_EMBEDDING_CACHE_DIR = KB_FILE.parent / ".cache" / "embedding"
_SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", "12.0"))
_AMBIGUOUS_REFERENT_MARKERS = [
    "这个", "那个", "这瓶", "那瓶", "这桶", "这个柜子", "那个柜子", "这里", "那里", "这种情况",
]
_FORCE_MORE_INFO_PATTERNS = [
    "过夜反应", "无人值守", "晚上可以回家", "能回家吗", "最适合替代", "替代二氯甲烷", "替代溶剂",
    "这个柜子里", "能不能放这里", "这个能不能放", "那个能不能放",
]

_QUERY_ANCHOR_GROUPS = [
    ("liquid_chromatography", ["hplc", "uhplc", "高效液相色谱", "液相色谱"]),
    ("biosafety_cabinet", ["生物安全柜", "biosafety cabinet", "bsc"]),
    ("muffle_furnace", ["马弗炉", "muffle furnace"]),
    ("power_outage", ["突然停电", "实验室停电", "停电应急", "power outage"]),
    ("high_voltage_supply", ["高压电源"]),
    ("reactive_metal", ["钠金属", "金属钠", "活泼金属"]),
    ("autoclave", ["高压灭菌锅", "高压灭菌器", "灭菌锅", "autoclave"]),
    ("oscilloscope", ["示波器"]),
    ("vacuum_pump", ["真空泵"]),
    ("nmr", ["核磁共振", "nmr"]),
    ("hydrofluoric_acid", ["氢氟酸", "hydrofluoric"]),
    ("diethyl_ether", ["乙醚", "diethyl ether"]),
    ("chemical_spill", ["泄漏", "洒漏", "打翻", "溅洒", "洒在", "洒出", "泼洒", "溢出"]),
    ("drying_oven", ["烘箱", "干燥箱"]),
    # 低温液体：不加这一组时，"液氮罐压力异常升高"的 BM25 top1 会落到
    # GC-MS 氢气载气/ICP-MS 钢瓶/DSC 高压坩埚这类同样含"压力/气瓶"的条目，
    # 把无关来源当成"参考依据"列出来。
    ("cryogenic_liquid", ["液氮", "液氦", "杜瓦", "低温液体", "深冷", "cryogen"]),
]
_INCIDENT_ANCHOR_NAMES = {"chemical_spill"}


def _filter_entries_by_query_anchor(
    question: str, entries: list[dict[str, str]]
) -> list[dict[str, str]]:
    q = normalize_search_text(question)
    active_groups = [
        (name, terms)
        for name, terms in _QUERY_ANCHOR_GROUPS
        if any(normalize_search_text(term) in q for term in terms)
    ]
    if not active_groups:
        return entries

    # 事故动作比物质名更能决定答案场景。例如“乙醚洒在台面上”同时激活
    # 乙醚和泄漏；如果要求一条 KB 同时在标题/标签中出现二者，可能无命中而
    # 回退到全库，导致一般乙醚操作条目排在真正的泄漏处置之前。
    required_groups = [
        terms for name, terms in active_groups if name in _INCIDENT_ANCHOR_NAMES
    ] or [terms for _name, terms in active_groups]

    anchored = []
    for row in entries:
        row_text = normalize_search_text(
            " ".join(
                [
                    row.get("title", ""),
                    row.get("question", ""),
                    row.get("tags", ""),
                    row.get("category", ""),
                    row.get("subcategory", ""),
                    row.get("hazard_types", ""),
                ]
            )
        )
        if all(
            any(normalize_search_text(term) in row_text for term in terms)
            for terms in required_groups
        ):
            anchored.append(row)
    return anchored or entries


def retrieve_citations(question: str, top_k: int = DEFAULT_TOP_K) -> list[Citation]:
    entries = _filter_entries_by_query_anchor(question, get_kb_entries())

    # ---- 语义检索（可选） ----
    semantic_scores: dict[str, float] = {}
    if _EMBEDDING_AVAILABLE and entries:
        try:
            mtime = os.path.getmtime(KB_FILE) if KB_FILE.exists() else 0.0
            texts = [
                " ".join(
                    [
                        row.get("title", ""),
                        row.get("question", ""),
                        row.get("answer", ""),
                        row.get("steps", ""),
                        row.get("forbidden", ""),
                        row.get("emergency", ""),
                        row.get("ppe", ""),
                        row.get("hazard_types", ""),
                        row.get("tags", ""),
                    ]
                )
                for row in entries
            ]
            semantic_results = semantic_search(
                query=question,
                entries=entries,
                texts=texts,
                cache_dir=_EMBEDDING_CACHE_DIR,
                kb_file_mtime=mtime,
                top_k=max(1, top_k) * 3,
            )
            if semantic_results:
                for score, row in semantic_results:
                    semantic_scores[row.get("id", "")] = score
        except Exception as exc:
            logger.warning("semantic_search failed, fallback to text search: %s", exc)

    # ---- 文本检索（原有逻辑） ----
    q = normalize_search_text(question)
    q_tokens = extract_tokens(question)
    scored: list[tuple[float, dict[str, str]]] = []
    for row in entries:
        score = 0.0
        row_question = normalize_search_text(row.get("question", ""))
        row_title = normalize_search_text(row.get("title", ""))
        if row_question and row_question == q:
            score += 10.0
        elif row_question and (row_question in q or q in row_question):
            score += 5.2
        if row_title and row_title == q:
            score += 8.0
        elif row_title and (row_title in q or q in row_title):
            score += 4.0
        title_tokens = row.get("title_tokens", set())
        tag_tokens = row.get("tag_tokens", set())
        body_tokens = row.get("body_tokens", set())
        all_tokens = row.get("all_tokens", set())
        for token in q_tokens:
            if token in title_tokens:
                score += 1.9 + min(len(token), 4) * 0.2
            elif token in tag_tokens:
                score += 1.35 + min(len(token), 4) * 0.15
            elif token in body_tokens:
                score += 0.95 + min(len(token), 4) * 0.11
            elif token in all_tokens:
                score += 0.65 + min(len(token), 4) * 0.08

        # ---- 混合加权：语义分数加成 ----
        sem_score = semantic_scores.get(row.get("id", ""), 0.0)
        if sem_score > 0:
            score += sem_score * _SEMANTIC_WEIGHT

        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = scored[: max(1, top_k)]
    if not selected:
        selected = [(0.1, row) for row in get_kb_entries()[: max(1, top_k)]]

    citations: list[Citation] = []
    for score, row in selected:
        snippet = " ".join(
            part for part in [row.get("answer", ""), row.get("steps", ""), row.get("forbidden", "")] if part
        )[:220]
        citations.append(
            Citation(
                kb_id=row.get("id", ""),
                title=row.get("title", ""),
                source_title=row.get("source_title", ""),
                source_org=row.get("source_org", ""),
                source_url=row.get("source_url", ""),
                risk_level=row.get("risk_level", ""),
                snippet=snippet,
                score=round(score, 3),
                steps=row.get("steps", ""),
                forbidden=row.get("forbidden", ""),
                first_aid=row.get("first_aid", ""),
                emergency=row.get("emergency", ""),
            )
        )
    return citations


def match_rule(question: str) -> dict[str, Any] | None:
    q = normalize_search_text(question)
    has_emergency_intent = any(
        marker in q for marker in EMERGENCY_INTENT_MARKERS
    ) or has_casualty_report(question)
    has_refuse_intent = any(marker in q for marker in REFUSE_INTENT_MARKERS)
    best: dict[str, Any] | None = None
    for order, rule in enumerate(get_rules_config().get("rules") or []):
        if not isinstance(rule, dict):
            continue
        patterns = [str(item).strip() for item in (rule.get("patterns") or []) if str(item).strip()]
        hits = [pattern for pattern in patterns if normalize_search_text(pattern) in q]
        if not hits:
            continue
        severity = str(rule.get("severity") or "low").lower()
        action = str(rule.get("action") or "safe_answer")
        enforcement = str(rule.get("enforcement") or "")
        # 同一严重度下，优先选择与用户当前意图一致的规则。
        # 1) action 跟用户当前意图对齐时给正分（3/2/1），让它们胜过同 severity
        #    的“沉默候选”。
        # 2) action 跟用户当前意图不对齐时给负分（-1），让
        #    ``direct_safe_answer`` / ``ask_for_more_info`` 等更贴合的规则
        #    能压过它。例如：query 是“钠金属应该如何安全储存？”没有
        #    ``EMERGENCY_INTENT_MARKERS``，R-026（redirect_emergency, critical）
        #    不该压过 R-027（direct_safe_answer, high）这条专门的 storage
        #    规则；再如 R-002（refuse）只在用户有“可以吗/能不能”等 refuse
        #    意图或 enforcement=always 时才该压过其它候选。
        # 否则像“乙醚泄漏后头晕怎么办”会因为 R-002 在 YAML 中排得更早而
        # 落到“禁止明火加热”，压过真正需要的泄漏/吸入应急规则。
        # ``enforcement: always`` 表示"命中即触发，不再要求问句里另有意图关键词"。
        # 对 redirect_emergency 而言，这适用于 patterns 本身就是事故描述的规则
        # （如 R-030"昏迷/不省人事"、R-031"液氮罐超压"）：用户写"同事昏迷不醒"
        # 就已经是在报事故了，不该因为句子里没有"怎么办"就被判成非应急。
        always_enforced = enforcement.strip().lower() == "always"
        intent_priority = 0
        if action == "redirect_emergency":
            intent_priority = 3 if (has_emergency_intent or always_enforced) else -1
        elif action == "refuse":
            if has_refuse_intent or always_enforced:
                intent_priority = 2
            else:
                intent_priority = -1
        elif action in {"ask_for_more_info", "direct_safe_answer"}:
            intent_priority = 1
        # intent_alignment 作为排序元组的第一维：当 action 跟用户当前意图
        # 不对齐（如 redirect_emergency 没有 emergency marker、refuse 没有
        # refuse marker 且 enforcement 不是 always）时降到 0；否则 1。这一
        # 维的优先级高于 severity，专门防止“高 severity 但 action 错配”的
        # 规则压过“低 severity 但 action 贴切”的规则，例如 R-026（critical,
        # redirect_emergency）在 storage query 里压过 R-027（high,
        # direct_safe_answer）。
        intent_alignment = 1
        if action == "redirect_emergency" and not (has_emergency_intent or always_enforced):
            intent_alignment = 0
        elif action == "refuse" and not (has_refuse_intent or always_enforced):
            intent_alignment = 0
        candidate = {
            "id": str(rule.get("id") or ""),
            "action": action,
            "severity": severity,
            "response": str(rule.get("response") or ""),
            "enforcement": enforcement,
            "score": (
                intent_alignment,
                SEVERITY_SCORE.get(severity, 1),
                intent_priority,
                len(hits),
                -order,
            ),
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def should_enforce_terminal_rule(question: str, rule: dict[str, Any] | None) -> bool:
    if not rule:
        return False
    action = str(rule.get("action") or "").strip()
    if action not in TERMINAL_ACTIONS:
        return False
    q = normalize_search_text(question)
    category = str(rule.get("id") or "")

    if action in {"ask_for_more_info", "direct_safe_answer"}:
        return True

    if action == "refuse":
        if str(rule.get("enforcement") or "").strip().lower() == "always":
            return True
        return any(marker in q for marker in REFUSE_INTENT_MARKERS)

    if action == "redirect_emergency":
        # 与 match_rule 一致：enforcement=always 的应急规则命中即触发，不再
        # 要求问句里另有 EMERGENCY_INTENT_MARKERS。用于"同事昏迷不醒"这类
        # 本身就是事故陈述、却不含"怎么办"的输入。
        if str(rule.get("enforcement") or "").strip().lower() == "always":
            return True
        return any(marker in q for marker in EMERGENCY_INTENT_MARKERS) or has_casualty_report(question)

    return False


def should_force_more_info(question: str, rule: dict[str, Any] | None = None) -> bool:
    q = normalize_search_text(question)
    if not q:
        return False

    if any(pattern in q for pattern in _FORCE_MORE_INFO_PATTERNS):
        return True

    if any(marker in q for marker in _AMBIGUOUS_REFERENT_MARKERS):
        if any(token in q for token in ["能不能", "可不可以", "可以吗", "怎么处理", "怎么办", "直接倒", "放在", "放这里", "放里面"]):
            return True

    if rule and str(rule.get("id") or "") == "R-003" and any(marker in q for marker in _AMBIGUOUS_REFERENT_MARKERS):
        return True

    return False

