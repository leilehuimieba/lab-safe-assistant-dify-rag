from __future__ import annotations

"""答案构建与低置信度处理服务

- assess_low_confidence: 根据引用分数判断是否为低置信度查询
- append_low_confidence_followup: 将低置信度问题写入待补强队列 CSV
- build_rule_answer: 按匹配规则生成标准化安全回答
- build_fallback_lab_answer: 在上游服务不可用时生成结构化回退回答
- append_low_confidence_followup_notice: 在回答末尾追加低置信度提示附注
- looks_truncated: 判断上游回答是否疑似因长度限制被截断
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



# DeepSeek's answers commonly end in one of several ways that are NOT
# truncation even though they don't end in "." or "。":
#   - a bare bolded list item, e.g. "...-**丙酮废液如何处理**" (ends in "*")
#   - a closing Chinese quote, e.g. "...“呼吸防护设备选择对照表”" (ends in "”")
# A prior version of this heuristic tried to strip a trailing "如果你愿意/如果需要..."
# offer-to-elaborate clause before checking, on the theory that it's always an
# unpunctuated sign-off tacked onto a complete answer. That's wrong in general:
# the offer clause is often itself a complete, properly punctuated sentence
# (e.g. "...如果你愿意，我还可以进一步整理成“...”简明版。"), and stripping it discarded
# that trailing "。" and inspected the wrong (unpunctuated list item) character
# instead, producing false positives. Simplest correct fix: just look at the
# actual last character of the actual last thing the model wrote.
_SENTENCE_END_CHARS = "。！？；.!?;\"')）】》」』*“”‘’"


def looks_truncated(answer: str) -> bool:
    """Heuristic: flag Dify-generated answers that stop mid-sentence (hit a
    token/length limit) instead of ending on normal closing punctuation."""
    text = (answer or "").strip()
    if not text:
        return False
    return text[-1] not in _SENTENCE_END_CHARS


def append_truncation_notice(answer: str) -> str:
    note = "附注：本回答可能因生成长度限制被截断，请核实关键安全步骤是否完整，必要时联系实验室安全管理人员确认。"
    text = (answer or "").strip()
    if not text or note in text:
        return text or note
    return f"{text}\n\n{note}"


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


def _build_refuse_fallback_answer(rule: dict[str, Any]) -> str:
    """Return a refusal template honoring the matched rule's response.

    Used as a safety net by build_fallback_lab_answer when a refuse-class
    rule (self-harm, prompt injection, etc.) somehow reaches the fallback
    path. The chat route normally intercepts these earlier, but we keep
    this so a future refactor cannot accidentally soften the refusal.
    """
    response = str(rule.get("response") or "该问题不在本助手服务范围内,无法提供帮助。").strip()
    return (
        "结论:\n"
        f"{response}\n"
    )


def _build_out_of_scope_answer(question: str) -> str:
    """Return a polite out-of-scope template for unrelated questions.

    Triggered when no safety rule matched and the local KB returned no
    citations: a clear signal that the question is outside the lab safety
    service. The original question is NOT echoed in the body to avoid
    surface area for prompt injection or accidental amplification.
    """
    return (
        "结论:\n"
        "这个问题不在实验室安全助手的服务范围内,不会按安全场景作答。\n\n"
        "我可以帮你处理以下问题:\n"
        "1. 化学品安全:储存、使用、泄漏、废液、混合禁忌\n"
        "2. 应急处置:火灾、触电、中毒、切割、辐射、液氮冻伤等\n"
        "3. 个人防护与实验室日常规范:PPE、通风柜、准入、培训\n"
        "4. 实验设备:通风柜、离心机、HPLC、液氮、马弗炉、气瓶等\n\n"
        "如需其他领域(天气、娱乐、编程、日常咨询等)的帮助,请使用对应场景的工具或资源。"
    )


def _build_emergency_rule_answer(rule_id: str, response: str, citations: list[Citation]) -> str:
    # rule.response 只填入"结论"段；立即处理/禁止事项/应急升级为本函数硬编码模板。
    # 覆盖 R-008、R-011~R-022 及特殊金属火灾 R-026；其他规则走末尾通用兜底。
    if rule_id == "R-008":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 先呼救并让他人联系急救；在未切断电源前，不要直接接触伤者或带电设备。\n"
            "2. 优先通过急停、断路器或总开关切断电源；无法确认断电或涉及高压时，立即撤离并等待专业人员。\n"
            "3. 确认断电且环境安全后，检查伤者意识和呼吸；无正常呼吸时由受训人员立即实施心肺复苏并使用 AED。\n"
            "4. 即使伤者看似恢复，也应尽快接受医疗评估，并保留设备和现场供事故调查。\n\n"
            "禁止事项:\n"
            "- 禁止直接触碰仍与电源接触的伤者。\n"
            "- 禁止用金属、潮湿物品或徒手移开带电导体。\n"
            "- 禁止在未验电、未隔离储能部件时擅自恢复供电或拆修设备。\n\n"
            "应急升级:\n"
            "- 涉及高压、电弧、烧伤、意识异常或呼吸心跳异常时，立即按严重电气伤害呼叫急救和专业电气人员。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-026":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止操作，警示周围人员远离，并切断附近可安全切断的热源或点火源。\n"
            "2. 仅在火势很小、退路畅通且你受过培训时，使用明确适用于金属火灾的D类灭火剂；没有专用灭火剂时可用大量干燥砂土覆盖窒息。\n"
            "3. 保持距离观察，防止复燃；火势扩大或灭火物资不匹配时立即撤离、关门隔离并报警。\n"
            "4. 向负责人和消防人员明确说明燃烧物是金属钠、钾等遇水反应物。\n\n"
            "禁止事项:\n"
            "- 禁止用水、湿砂、泡沫或任何含水灭火剂。\n"
            "- 禁止使用二氧化碳灭火器处置金属钠、钾火灾。\n"
            "- 禁止徒手搬动燃烧物、用脚踩压或在不确定灭火剂相容性时盲目扑救。\n\n"
            "应急升级:\n"
            "- 火势无法立即控制、涉及较大数量活泼金属或邻近其他危化品时，立即按重大危化品火灾撤离并等待专业消防力量。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-011":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立刻停止操作，用大量流动清水持续冲洗受污染皮肤至少 15 分钟。\n"
            "2. 冲洗同时尽快脱去被污染的手套、袖套、实验服和饰物，避免继续接触皮肤。\n"
            "3. 氢氟酸（HF）暴露即使症状轻微也必须立即就医并准备葡萄糖酸钙凝胶；如为其他强酸、强碱或出现持续疼痛、发白、起泡、麻木，应在冲洗后立即就医并告知化学品名称。\n\n"
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
            "1. 立刻使用洗眼器或大量清水持续冲洗至少 15 分钟，越早越好。\n"
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
            "- 如涉及危化品、气瓶、锂电池或有人受伤，直接按重大实验室火灾处置并等待专业力量到场。\n"
            "- 燃烧物是金属钠、钾、镁等活泼金属时立即改用 D 类灭火剂或干燥砂土覆盖，禁止用水和普通灭火器（详见金属火灾专项处置）。\n"
            "- 火源疑似电气短路或带电设备时，先切断电源再处置，禁止直接用水或泡沫灭火。\n\n"
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
            "- 若有人出现头晕、咳嗽、呼吸困难等暴露症状，立即转移到新鲜空气处并联系医疗支持；现场通风不足或存在起火/爆炸风险时，立即启动应急预案并联系专业救援力量。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-016":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止进食或饮水，清除口腔内残留物；如人清醒，可用清水轻轻漱口后吐出。\n"
            "2. 立即联系医疗急救或中毒咨询支持，并准备化学品标签、SDS、浓度、摄入时间和估计摄入量。\n"
            "3. 按 SDS 和医务人员指示处置；保持人员安静并持续观察意识、呼吸和呕吐情况。\n"
            "4. 若意识不清、抽搐、呼吸困难或无法安全吞咽，立即呼叫急救并将其置于安全侧卧位，禁止经口喂任何东西。\n\n"
            "禁止事项:\n"
            "- 禁止催吐，除非专业医疗人员明确要求。\n"
            "- 禁止擅自喂水、牛奶、中和剂、活性炭或其他食物饮料。\n"
            "- 禁止让意识不清或抽搐者经口摄入任何东西。\n\n"
            "应急升级:\n"
            "- 涉及腐蚀性、高毒、未知化学品或出现意识/呼吸异常时，按危重中毒立即送医并携带 SDS 或容器信息。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-017":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止操作并离开污染区域，转移到新鲜空气处；救援者不得在没有合适防护的情况下进入污染区。\n"
            "2. 让暴露人员保持安静和保暖，松开紧身衣物，持续观察意识、呼吸、咳嗽和胸闷变化。\n"
            "3. 立即报告实验室负责人，并准备化学品标签、SDS、暴露时间和可能浓度供医务人员判断。\n"
            "4. 出现呼吸困难、意识异常、持续头晕或症状加重时，立即呼叫急救；无正常呼吸时由受训人员实施急救。\n\n"
            "禁止事项:\n"
            "- 禁止让暴露人员独自返回污染区取物或继续实验。\n"
            "- 禁止救援者在无呼吸防护、无监护时贸然进入高浓度或未知气体区域。\n"
            "- 禁止因暂时好转而忽略可能延迟出现的呼吸道症状。\n\n"
            "应急升级:\n"
            "- 多人暴露、有毒气体、大量挥发性溶剂或密闭空间事件，应立即扩大疏散范围并等待专业救援和监测确认安全。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-018":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止热源接触，用凉的流动清水持续冷却伤处约 20 分钟。\n"
            "2. 冷却过程中移除戒指、手表等紧束物；粘在皮肤上的衣物不要强行撕下。\n"
            "3. 冷却后用无粘性无菌敷料或洁净保鲜膜松散覆盖，保持伤处清洁。\n"
            "4. 面部、眼部、手部、关节、会阴、大面积或深度烧伤，以及出现水泡、焦黑、剧痛时尽快就医。\n\n"
            "禁止事项:\n"
            "- 禁止直接冰敷或使用冰水，以免进一步损伤组织。\n"
            "- 禁止涂牙膏、油脂、药膏或自行挑破水泡。\n"
            "- 禁止撕扯与皮肤粘连的衣物。\n\n"
            "应急升级:\n"
            "- 伴随吸入烟气、意识异常、呼吸困难或大面积烧伤时，立即呼叫急救。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-019":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 先戴手套保护救助者，用无菌纱布或洁净布对伤口持续直接加压止血。\n"
            "2. 出血控制后，用清水冲洗表面污染并覆盖无菌敷料；持续出血时不要反复掀开首层敷料查看，可在上方继续加垫加压。\n"
            "3. 如伤口内有较大玻璃、金属等嵌入异物，不要拔除，应围绕异物固定并尽快就医。\n"
            "4. 记录污染物、破损器具和暴露经过；涉及生物材料、化学品或锐器伤时同步启动职业暴露评估。\n\n"
            "禁止事项:\n"
            "- 禁止用力探查伤口或自行拔除深部异物。\n"
            "- 禁止用口接触伤口，也不要把污染伤口长期浸泡在刺激性消毒液中。\n"
            "- 禁止在明显大量出血、麻木或活动受限时拖延就医。\n\n"
            "应急升级:\n"
            "- 直接加压仍无法止血、喷射样出血、伤口很深或伤者出现苍白头晕时，立即呼叫急救并持续加压。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-020":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止作业，警示并疏散无关人员，关闭或隔离区域，避免污染扩散。\n"
            "2. 不擅自触碰、搬动或寻找丢失放射源；立即通知本单位辐射安全负责人和许可证授权人员。\n"
            "3. 疑似人员污染时，按辐射安全人员指示脱去外层污染衣物并装袋隔离；皮肤污染用温和的清水和肥皂清洗，避免用力擦伤皮肤。\n"
            "4. 记录人员、核素、活度、时间、地点和可能扩散路径，配合专业人员监测、去污和剂量评估。\n\n"
            "禁止事项:\n"
            "- 禁止未授权人员进入隔离区或自行清扫、拖洗污染物。\n"
            "- 禁止把污染物带离现场、倒入下水道或混入普通废物。\n"
            "- 禁止在未监测确认前解除警戒或恢复工作。\n\n"
            "应急升级:\n"
            "- 按本单位许可证、应急预案和属地监管要求，由辐射安全负责人决定外部报告和专业支援；不使用脱离具体情境的固定时限替代法定流程。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-021":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止操作并关闭激光，警示现场人员；不要改变光路和设备设置，以便后续调查。\n"
            "2. 保持伤者安静，避免继续接触强光；记录激光波长、功率/能量、脉冲特性、暴露距离和时间。\n"
            "3. 尽快接受眼科评估；出现视野黑点、闪光、视力下降、疼痛或畏光时按紧急眼伤处理。\n"
            "4. 同步通知实验室负责人和激光安全负责人，封控设备直至完成调查和重新授权。\n\n"
            "禁止事项:\n"
            "- 禁止揉眼、压迫眼球或自行滴用不明眼药水。\n"
            "- 激光暴露不是化学品入眼，眼部冲洗不是默认处置；仅在同时存在化学污染时按化学眼暴露流程处理。\n"
            "- 禁止在事故调查和安全确认前重新开启激光或改动现场。\n\n"
            "应急升级:\n"
            "- 任何疑似 3B/4 类激光眼暴露或出现视觉症状时，应尽快由眼科专业人员评估。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-022":
        return (
            "结论:\n"
            f"{response}\n\n"
            "立即处理:\n"
            "1. 立即停止接触，移除未与皮肤冻结粘连的手套、衣物和饰物；粘住的材料不要强行撕下。\n"
            "2. 将冻伤部位置于温水中缓慢复温，水温不超过 40°C；复温后用干燥无菌敷料松散覆盖。\n"
            "3. 保持伤者温暖和安静，严重疼痛、水泡、皮肤发白/发黄或感觉异常时立即就医。\n"
            "4. 如液氮大量泄漏在密闭空间，所有人员立即撤离，等待氧含量和通风条件经专业人员确认。\n\n"
            "禁止事项:\n"
            "- 禁止揉搓、按摩冻伤部位或刺破水泡。\n"
            "- 禁止直接火烤、热风吹、贴暖宝宝或使用超过 40°C 的热水快速加热。\n"
            "- 禁止在可能缺氧的区域内单人返回救援或查漏。\n\n"
            "应急升级:\n"
            "- 涉及眼部、大片皮肤、意识异常或疑似缺氧时，立即呼叫急救并启动低温液体泄漏应急预案。\n\n"
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
    if rule_id == "R-028":
        return (
            "结论:\n"
            f"{response}\n\n"
            "常见禁止行为:\n"
            "1. 禁止在实验区饮食、饮水、吸烟、嚼口香糖或存放食品，食品不得放入实验室冰箱。\n"
            "2. 禁止穿拖鞋、凉鞋、短裤或其他暴露皮肤的服装进入化学实验区；不得省略护目镜、实验服和所需手套。\n"
            "3. 禁止未经培训和授权独自开展高风险实验，禁止让反应、加热、高压或旋转设备无人值守。\n"
            "4. 禁止带电插拔、绕过联锁、在通风柜失效时继续操作，禁止将危废倒入下水道或普通垃圾桶。\n"
            "5. 禁止隐瞒泄漏、受伤、设备报警和险情；发现异常应立即停止、隔离并报告。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-029":
        return (
            "结论:\n"
            f"{response}\n\n"
            "下班前安全检查:\n"
            "1. 确认所有反应、加热设备、烘箱、马弗炉和其他非必要电器已按SOP停止；确需连续运行的设备已审批、标识并落实巡查。\n"
            "2. 关闭不再使用的气瓶阀门和气源，检查减压阀、软管及现场无泄漏报警。\n"
            "3. 清理通风柜操作区，密闭化学品和废液容器，将前窗降至安全位置；按本单位要求保持或关闭排风。\n"
            "4. 完成水电检查：关闭不需要的水源、电源和插座负载，确认无滴漏、过热、异味或异常声响。\n"
            "5. 危化品归位、危废分类密闭并贴签，清理通道和台面，关好门窗，完成安全检查记录后方可离开。\n\n"
            "禁止事项:\n"
            "- 禁止用断总电代替逐项确认，也禁止关闭必须维持的通风、冷藏、监测或联锁系统。\n"
            "- 禁止未审批的过夜反应和无人值守高风险设备。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
    if rule_id == "R-027":
        return (
            "结论:\n"
            f"{response}\n\n"
            "步骤:\n"
            "1. 储存前核对SDS和容器标签，确认对象确为金属钠、钾等遇水反应物。\n"
            "2. 金属钠通常浸没在合适的干燥矿物油或专用惰性覆盖介质中，使用密闭、完好、清晰标识的容器，置于阴凉干燥且远离水源的位置。\n"
            "3. 取用时保持工具和操作环境干燥，小量操作，并准备适用的D类灭火剂或干燥砂土。\n"
            "4. 剩余物、受污染覆盖油和废料不得自行加水销毁，应密闭标识后交由本单位危废流程和受训人员处置。\n\n"
            "禁止事项:\n"
            "- 禁止接触水、潮湿空气、酸或含水废液；遇水可产生氢气并引发火灾。\n"
            "- 禁止裸露存放、使用潮湿工具或与普通化学品废物混装。\n"
            "- 禁止用水或二氧化碳灭火器处理金属钠、钾火灾。\n\n"
            "参考依据:\n"
            f"{format_citation_lines(citations)}"
        )
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


def _split_semi_list(text: str) -> list[str]:
    return [part.strip() for part in (text or "").replace("；", ";").split(";") if part.strip()]


def build_fallback_lab_answer(
    question: str,
    citations: list[Citation],
    rule: dict[str, Any] | None = None,
    low_confidence_reason: str = "",
) -> str:
    # Short-circuit 1: refuse-class rule (e.g. R-006 self-harm, R-007 prompt
    # injection) must never be silently overridden by a generic safety
    # template, even when called from the fallback path. The chat route
    # normally intercepts these via should_enforce_terminal_rule, but if a
    # refactor ever routes them here, honor the refusal explicitly.
    if rule is not None and str(rule.get("action") or "").strip() == "refuse":
        return _build_refuse_fallback_answer(rule)

    # Short-circuit 2: out-of-scope. If neither a rule matched nor any KB
    # citation surfaced, the question is unrelated to laboratory safety.
    # Returning a generic "按 SOP 处理" answer would look nonsensical to the
    # user (e.g. "1+1=?" getting a four-section safety reply). Politely
    # decline and describe the actual service scope instead.
    if rule is None and not citations:
        return _build_out_of_scope_answer(question)

    highest_risk = max(
        [int(float(item.risk_level)) for item in citations if str(item.risk_level).replace(".", "", 1).isdigit()] or [3]
    )
    risk_text = RISK_LABEL.get(highest_risk, "Medium")
    top = citations[0] if citations else None
    top_title = top.title if top else "No direct KB match"
    notes = low_confidence_reason or "upstream unavailable"
    guard = str((rule or {}).get("response") or "").strip()

    kb_steps = _split_semi_list(top.steps) if top else []
    kb_first_aid = _split_semi_list(top.first_aid) if top else []
    kb_forbidden = _split_semi_list(top.forbidden) if top else []
    kb_emergency = (top.emergency if top else "").strip()

    if kb_steps:
        step_lines = [f"{i}. {item}。" for i, item in enumerate(kb_steps, start=1)]
        if kb_first_aid:
            step_lines.append("若已发生伤害，参考急救处置：")
            step_lines.extend(f"- {item}。" for item in kb_first_aid)
        steps_block = "\n".join(step_lines)
    else:
        steps_block = (
            "1. 先暂停操作并隔离能量、反应或暴露源。\n"
            "2. 重新核对 PPE、围护、通风和应急设备状态。\n"
            "3. 按书面 SOP 执行，并明确一人控制、一人观察、一人上报。\n"
            "4. 如已出现受伤、起火、泄漏或异常反应，立即启动应急预案。"
        )

    if kb_forbidden:
        forbidden_block = "\n".join(f"- {item}。" for item in kb_forbidden)
    else:
        forbidden_block = (
            "- 未经授权或无人监护时禁止继续操作。\n"
            "- 禁止绕过通风、断电锁定、屏蔽或废弃物分类要求。\n"
            "- 禁止隐瞒异常情况或延迟上报。"
        )

    if kb_emergency:
        escalation_block = f"- {kb_emergency}。"
    else:
        escalation_block = (
            "- 人员受伤或暴露：先冲洗或隔离，再联系医疗支持。\n"
            "- 存在起火或爆炸风险：立即撤离并联系应急力量。\n"
            "- 存在泄漏：先警戒隔离，再按泄漏 SOP 处置。"
        )

    return (
        "结论:\n"
        f"请将该问题视为 {risk_text} 风险等级的实验室安全场景，优先依照本地 SOP 处理，不要临场 improvising。\n\n"
        "步骤:\n"
        f"{steps_block}\n\n"
        "禁止事项:\n"
        f"{forbidden_block}\n\n"
        "应急升级:\n"
        f"{escalation_block}\n\n"
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
