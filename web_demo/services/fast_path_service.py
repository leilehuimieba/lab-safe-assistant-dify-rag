from __future__ import annotations

import re
from typing import Any

from ..models import Citation
from ..repositories import get_kb_entries, normalize_search_text


FAST_PATH_KEYWORDS = [
    ("个人防护", ["个人防护", "ppe", "护目镜", "实验服", "手套", "口罩", "鞋", "穿戴"]),
    ("通风柜", ["通风柜", "排风柜", "风罩"]),
    ("废弃物", ["废弃物", "废液", "废试剂", "废瓶", "垃圾分类"]),
    ("基础应知", ["实验室前", "进入实验室", "注意事项", "基本要求"]),
]


def _matches_fast_path(question: str, citation: Citation) -> bool:
    q = normalize_search_text(question)
    title = normalize_search_text(citation.title)
    source = normalize_search_text(citation.source_title)
    for _, keywords in FAST_PATH_KEYWORDS:
        if any(keyword in q for keyword in keywords):
            if any(keyword in title or keyword in source for keyword in keywords):
                return True
    return False


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
    return [item.strip(" -—•·\t ") for item in parts if item.strip(" -—•·\t ")]


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
    if low_confidence or rule or not citations:
        return False
    top = citations[0]
    try:
        risk_level = int(float(top.risk_level or "0"))
    except ValueError:
        risk_level = 0
    if risk_level >= 4:
        return False
    if top.score < 8:
        return False
    return _matches_fast_path(question, top)


def build_fast_path_answer(question: str, citations: list[Citation]) -> str:
    top = citations[0]
    row = _lookup_kb_row(top.kb_id)

    answer = (row or {}).get("answer", "").strip()
    steps = _split_items((row or {}).get("steps", ""))
    forbidden = _split_items((row or {}).get("forbidden", ""))
    ppe = _split_items((row or {}).get("ppe", ""))
    emergency = _split_items((row or {}).get("emergency", ""))

    summary = _first_sentence(answer) or _first_sentence(top.snippet)
    if not summary:
        summary = "请按实验室基础安全要求完成个人防护、环境核对并遵循书面 SOP。"

    if not steps:
        steps = [
            "先按实验室基础安全要求完成个人防护与环境检查",
            "再对照对应设备或化学品的书面 SOP 执行",
            "如现场条件与常规流程不一致，先暂停并询问老师或安全员",
        ]

    if ppe and any(token in normalize_search_text(question) for token in ["个人防护", "ppe", "护目镜", "实验服", "手套", "口罩", "鞋"]):
        steps = [f"优先确认防护要求：{'、'.join(ppe[:4])}"] + steps[:2]

    if not forbidden:
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
