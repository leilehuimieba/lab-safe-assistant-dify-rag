from __future__ import annotations

"""答案构建与低置信度处理服务

- assess_low_confidence: 根据引用分数判断是否为低置信度查询
- append_low_confidence_followup: 将低置信度问题写入待补强队列 CSV
- build_rule_answer: 按匹配规则生成标准化安全回答
- build_fallback_lab_answer: 在上游服务不可用时生成结构化回退回答
- append_low_confidence_followup_notice: 在回答末尾追加低置信度提示附注
"""

import csv
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import Citation
from ..repositories import (
    DEFAULT_LOW_CONFIDENCE_TOP_SCORE,
    RISK_LABEL,
    QUEUE_HEADERS,
    LOW_CONFIDENCE_QUEUE_FILE,
    normalize_search_text,
    safe_read_csv_rows,
    write_csv_row,
    _QUEUE_LOCK,
)


def assess_low_confidence(citations: list[Citation]) -> tuple[bool, str]:
    if not citations:
        return True, "no_kb_match"
    threshold = float(os.getenv("LOW_CONFIDENCE_TOP_SCORE", str(DEFAULT_LOW_CONFIDENCE_TOP_SCORE)))
    if citations[0].score < threshold:
        return True, f"top_score_below_threshold:{citations[0].score}<{threshold}"
    return False, ""


def append_low_confidence_followup(
    *,
    question: str,
    mode: str,
    decision: str,
    risk_level: str,
    matched_rule_id: str,
    matched_rule_action: str,
    low_confidence_reason: str,
    citations: list[Citation],
    queue_file: Path = LOW_CONFIDENCE_QUEUE_FILE,
) -> bool:
    question_norm = normalize_search_text(question)
    if not question_norm:
        return False
    question_hash = hashlib.sha1(question_norm.encode("utf-8")).hexdigest()
    queue_file.parent.mkdir(parents=True, exist_ok=True)

    with _QUEUE_LOCK:
        existing_hashes: set[str] = set()
        if queue_file.exists():
            with queue_file.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    value = (row.get("question_hash") or "").strip()
                    if value:
                        existing_hashes.add(value)
        if question_hash in existing_hashes:
            return False

        top = citations[0] if citations else None
        write_csv_row(
            queue_file,
            QUEUE_HEADERS,
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "question_hash": question_hash,
                "question": question.strip(),
                "mode": mode,
                "decision": decision,
                "risk_level": risk_level,
                "matched_rule_id": matched_rule_id,
                "matched_rule_action": matched_rule_action,
                "low_confidence_reason": low_confidence_reason,
                "citation_count": str(len(citations)),
                "top_score": str(top.score if top else ""),
                "top_kb_id": top.kb_id if top else "",
                "top_source_title": top.source_title if top else "",
                "suggested_lane": "collector",
                "suggested_action": "add_or_rewrite_kb_entry",
                "status": "open",
                "notes": "",
            },
        )
    return True


def format_citation_lines(citations: list[Citation], limit: int = 3) -> str:
    if not citations:
        return "- no direct KB citation"
    return "\n".join(f"- {item.kb_id}: {item.source_title or item.title or '-'}" for item in citations[:limit])


def _build_emergency_rule_answer(rule_id: str, response: str, citations: list[Citation]) -> str:
    # rule.response 只填入"结论"段；立即处理/禁止事项/应急升级为本函数硬编码模板。
    # 覆盖 R-011~R-020；未列出的 redirect_emergency 规则走末尾通用兜底。
    if rule_id == "R-011":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立刻停止操作，用大量流动清水持续冲洗受污染皮肤至少 15 分钟。\n"
            "2. 冲洗同时尽快脱去被污染的手套、袖套、实验服和饰物，避免继续接触皮肤。\n"
            "3. 如为强酸、强碱、HF 或出现持续疼痛、发白、起泡、麻木，应在冲洗后立即就医并告知化学品名称。\n\n"
            "禁止事项:\n"
            "- 禁止先找中和剂再冲洗，冲洗优先。\n"
            "- 禁止揉搓患处或继续穿戴被污染衣物。\n"
            "- 禁止因症状暂时不明显而延误报告和就医。\n\n"
            "应急升级:\n"
            "- 如污染面积大、化学品毒性强或伴随吸入暴露，立即呼叫他人协助并启动实验室应急预案。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-012":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立刻使用洗眼器或大量清水冲洗15分钟以上，越早越好。\n"
            "2. 冲洗时用手指撑开眼睑，并让眼球转动，确保结膜囊和眼球各部位都被冲到。\n"
            "3. 如佩戴隐形眼镜且容易取下，可在冲洗过程中尽快取下；同时呼叫他人协助并准备化学品信息。\n"
            "4. 冲洗后立即就医，明确告知接触的化学品名称、浓度和接触时间。\n\n"
            "禁止事项:\n"
            "- 禁止揉眼睛。\n"
            "- 禁止自行使用中和液、有色液体或眼药水代替大量清水冲洗。\n"
            "- 禁止因症状减轻就中断冲洗或延误就医。\n\n"
            "应急升级:\n"
            "- 若出现视物模糊、持续疼痛、畏光或强酸强碱/有机溶剂暴露，按高优先级眼部化学伤处理并立即送医。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-013":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 第一时间停止实验，能安全做到时切断电源、气源并提醒周围人员撤离。\n"
            "2. 小火且你受过培训时，可在确认退路畅通的前提下使用就近灭火器或灭火毯处置初起火情。\n"
            "3. 若火势扩大、伴随浓烟/爆鸣或涉及气瓶、溶剂柜，立即关闭房门、撤离到安全区域并报警。\n"
            "4. 到集合点后报告实验室负责人，说明起火位置、涉及化学品/设备和是否有人受伤。\n\n"
            "禁止事项:\n"
            "- 禁止在火势失控时继续抢救仪器或样品。\n"
            "- 禁止在不了解火源类型时盲目泼水灭火。\n"
            "- 禁止乘坐电梯撤离或单人返回火场查看。\n\n"
            "应急升级:\n"
            "- 如涉及危化品、气瓶、锂电池或有人受伤，直接按重大实验室火灾处置并等待专业力量到场。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-014":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止实验，能安全做到时关闭气源阀门，禁止一切点火、插拔电器和产生火花的动作。\n"
            "2. 迅速通知周围人员撤离到上风或安全区域，并在门外做警示隔离。\n"
            "3. 在不增加暴露风险的前提下开启通风或保持原有排风，不要在污染区久留。\n"
            "4. 立即报告实验室负责人、物业或专业维保，说明气体种类、钢瓶编号和泄漏位置。\n\n"
            "禁止事项:\n"
            "- 禁止在泄漏区域开关灯、拔插插头或使用手机靠近泄漏点。\n"
            "- 禁止单人近距离长时间查漏。\n"
            "- 禁止在未确认安全前恢复实验。\n\n"
            "应急升级:\n"
            "- 如为有毒/可燃气体、多人闻到异味或疑似大量泄漏，立即扩大警戒范围并等待专业人员处置。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-015":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立刻停止周边操作，警示他人远离，优先隔离泄漏区并避免吸入蒸气或直接接触。\n"
            "2. 若为大量、未知成分、强挥发性、高毒、强腐蚀性或伴随冒烟反应的泄漏，立即疏散撤离、关门封控并报告，不要自行处理。\n"
            "3. 仅当泄漏量小、化学品已知且你受过培训时，才可在 PPE、SDS 和本地泄漏 SOP 指引下使用吸附棉、围堵条等泄漏包物资处理。\n"
            "4. 收集吸附物和污染耗材，按相应危废分类密封暂存；后续完成去污、上报和事件记录。\n\n"
            "禁止事项:\n"
            "- 禁止对大量或未知泄漏单人硬顶处理。\n"
            "- 禁止把泄漏物冲入下水道或直接用拖把扩散污染范围。\n"
            "- 禁止在未确认相容性的情况下混用中和剂、吸附剂或清洗剂。\n\n"
            "应急升级:\n"
            "- 若有人暴露、现场通风不足或存在起火/爆炸风险，立即启动实验室应急预案并联系专业救援力量。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    return (
        "结论:\n"
        f"{response}\n\n"
        "步骤:\n"
        "1. 立即停止当前操作并隔离危险源。\n"
        "2. 第一时间通知实验室负责人和安全联系人。\n"
        "3. 按本单位 SOP 执行现场控制、上报和记录。\n\n"
        "禁止事项:\n"
        "- 禁止继续开展当前高风险操作。\n"
        "- 禁止绕过通风、审批、联锁或 PPE 要求。\n\n"
        "应急升级:\n"
        "- 如存在受伤、起火、泄漏或暴露风险，立即启动应急预案。\n\n"
        "参考依据:\n"
        f"{format_citation_lines(citations)}"
    )


def build_rule_answer(rule: dict[str, Any], citations: list[Citation]) -> str:
    action = str(rule.get("action") or "").strip()
    rule_id = str(rule.get("id") or "").strip()
    response = str(rule.get("response") or "Stop the task and follow the local emergency procedure immediately.").strip()
    if action == "ask_for_more_info":
        return (
            "结论:\n"
            f"{response}\n\n"
            "请补充以下信息后我再继续判断：\n"
            "1. 具体试剂、设备或柜体对象是什么；\n"
            "2. 当前处于储存、使用、处置还是异常情况；\n"
            "3. 是否已经出现泄漏、受伤、冒烟、报警等紧急迹象。\n\n"
            "在信息不完整前：\n"
            "- 不要继续高风险操作；\n"
            "- 不要擅自混放、倾倒、开盖或离开现场；\n"
            "- 如已出现人员暴露或事故征兆，立即按应急预案处理。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if action == "direct_safe_answer":
        return (
            "结论:\n"
            f"{response}\n\n"
            "步骤:\n"
            "1. 先按化学品相容性重新核对危险特性，不要只看是否‘都能进柜’。\n"
            "2. 氧化性酸、易燃有机溶剂等不相容物质应分柜或分区隔离存放。\n"
            "3. 如现场柜体分类不明确，先暂停放置并联系实验室负责人确认。\n\n"
            "禁止事项:\n"
            "- 禁止将不相容化学品同柜、同层或紧邻混放。\n"
            "- 禁止在未核对标签、浓度和危险类别前凭经验判断可否共存。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if action == "redirect_emergency":
        return _build_emergency_rule_answer(rule_id, response, citations)
    return (
        "结论:\n"
        f"{response}\n\n"
        "步骤:\n"
        "1. 立即停止当前操作并隔离危险源。\n"
        "2. 第一时间通知实验室负责人和安全联系人。\n"
        "3. 按本单位 SOP 执行现场控制、上报和记录。\n\n"
        "禁止事项:\n"
        "- 禁止继续开展当前高风险操作。\n"
        "- 禁止绕过通风、审批、联锁或 PPE 要求。\n\n"
        "应急升级:\n"
        "- 如存在受伤、起火、泄漏或暴露风险，立即启动应急预案。\n\n"
        "参考依据:\n"
        f"{format_citation_lines(citations)}"
    )


def build_fallback_lab_answer(
    question: str,
    citations: list[Citation],
    rule: dict[str, Any] | None = None,
    low_confidence_reason: str = "",
) -> str:
    highest_risk = max(
        [int(float(item.risk_level)) for item in citations if str(item.risk_level).replace(".", "", 1).isdigit()] or [3]
    )
    risk_text = RISK_LABEL.get(highest_risk, "Medium")
    top_title = citations[0].title if citations else "No direct KB match"
    notes = low_confidence_reason or "upstream unavailable"
    guard = str((rule or {}).get("response") or "").strip()
    return (
        "结论:\n"
        f"请将该问题视为 {risk_text} 风险等级的实验室安全场景，优先依照本地 SOP 处理，不要临场 improvising。\n\n"
        "步骤:\n"
        "1. 先暂停操作并隔离能量、反应或暴露源。\n"
        "2. 重新核对 PPE、围护、通风和应急设备状态。\n"
        "3. 按书面 SOP 执行，并明确一人控制、一人观察、一人上报。\n"
        "4. 如已出现受伤、起火、泄漏或异常反应，立即启动应急预案。\n\n"
        "禁止事项:\n"
        "- 未经授权或无人监护时禁止继续操作。\n"
        "- 禁止绕过通风、断电锁定、屏蔽或废弃物分类要求。\n"
        "- 禁止隐瞒异常情况或延迟上报。\n\n"
        "应急升级:\n"
        "- 人员受伤或暴露：先冲洗或隔离，再联系医疗支持。\n"
        "- 存在起火或爆炸风险：立即撤离并联系应急力量。\n"
        "- 存在泄漏：先警戒隔离，再按泄漏 SOP 处置。\n\n"
        "参考依据:\n"
        f"- top context: {top_title}\n"
        f"{format_citation_lines(citations)}\n\n"
        "备注:\n"
        f"- fallback reason: {notes}\n"
        f"- guardrail: {guard or 'N/A'}\n"
        f"- original question: {question.strip()}"
    )


def append_low_confidence_followup_notice(answer: str) -> str:
    note = "附注：该问题已加入低置信待补强队列，后续会继续完善知识库。"
    text = (answer or "").strip()
    if not text or note in text:
        return text or note
    return f"{text}\n\n{note}"
