from __future__ import annotations

import csv
import logging
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from starlette.concurrency import run_in_threadpool

from ..models import ChatRequest, ChatResponse, FeedbackRequest, StatsResponse
from ..repositories import DEFAULT_TOP_K, DIFY_DEFAULT_TIMEOUT, REPO_ROOT
from ..services import (
    retrieve_citations, match_rule, should_enforce_terminal_rule, should_force_more_info,
    build_rule_answer, assess_low_confidence, append_low_confidence_followup,
    append_low_confidence_followup_notice, looks_truncated, append_truncation_notice, call_dify_lab,
    build_fallback_lab_answer, resolve_dify_api_base, build_dify_proxy_auth,
    get_or_create, set_conversation_id, add_history, get_cached_answer, set_cached_answer,
    select_fast_path_citations, build_fast_path_answer, use_local_complete_response,
)
from ..services.auth_service import verify_password
from ..services.kb_usage_service import record_kb_usage

router = APIRouter(dependencies=[Depends(verify_password)])

logger = logging.getLogger(__name__)


def _classify_dify_failure(detail: str) -> str:
    """把 call_dify_lab 抛出的 HTTPException.detail 归类成用户可读的中文短标签。

    目的：`structured_fallback` 兜底时保留“为什么回退”的可区分信息，便于事后
    根因排查（超时 / 上游空返回 / 上游报错 / 连接失败 / 配置错误），避免像此前那样
    所有回退都被记成同一句 "upstream unavailable" 而无法区分失败模式。
    仅返回稳定的短标签，不回传上游原始报文（原始 detail 另行写入服务端日志）。
    """
    text = (detail or "").lower()
    if "timeout" in text or "timed out" in text:
        return "上游响应超时"
    if "empty_answer" in text or "empty" in text:
        return "上游未返回有效内容"
    if "dify_http_" in text or "http " in text:
        return "上游返回错误"
    if "request_failed" in text or "connection" in text:
        return "上游连接失败"
    if "api_key" in text or "base_url" in text or "allowlist" in text:
        return "上游配置错误"
    return "上游暂时不可用"


# --- In-memory performance stats ---
_stats_lock = threading.Lock()
_recent_metrics: list[dict[str, float | bool]] = []  # last 200 requests
_MAX_STATS = 200

FEEDBACK_FILE = REPO_ROOT / "artifacts" / "user_feedback" / "feedback.csv"
FEEDBACK_HEADERS = ["created_at", "session_id", "question", "answer", "rating", "comment"]
_FEEDBACK_LOCK = threading.Lock()
_FEEDBACK_MAX_QUESTION = 2000
_FEEDBACK_MAX_COMMENT = 2000


def _dify_sse_chunk_size() -> int:
    """Small bounded chunks reduce proxy-side delay before the first SSE event."""
    raw = os.getenv("DIFY_SSE_PROXY_CHUNK_SIZE", "1").strip()
    try:
        configured = int(raw)
    except ValueError:
        configured = 1
    return max(1, min(4096, configured))


def _dify_sse_response_headers() -> dict[str, str]:
    """Prevent reverse proxies and GZipMiddleware from buffering SSE output."""
    return {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
        # Starlette's GZipMiddleware buffers streaming bodies when clients send
        # Accept-Encoding: gzip.  An explicit identity encoding makes it pass
        # SSE bytes through immediately instead.
        "Content-Encoding": "identity",
    }


def _extract_kb_ids(citations: list[Any]) -> list[str]:
    ids = []
    for c in citations:
        if hasattr(c, "kb_id") and getattr(c, "kb_id"):
            ids.append(getattr(c, "kb_id"))
        elif isinstance(c, dict) and c.get("kb_id"):
            ids.append(c["kb_id"])
    return ids


def _build_contextual_query(question: str, history: list[dict[str, str]]) -> str:
    recent = history[-2:]
    if not recent:
        return question
    parts = ["以下是同一用户刚刚的上下文，请结合上下文回答最后一个追问："]
    for idx, item in enumerate(recent, start=1):
        prev_q = str(item.get("question") or "").strip()
        prev_a = str(item.get("answer") or "").strip()
        if prev_q:
            parts.append(f"上一轮问题{idx}：{prev_q}")
        if prev_a:
            parts.append(f"上一轮回答{idx}：{prev_a[:300]}")
    parts.append(f"本轮追问：{question.strip()}")
    return "\n".join(parts)


def _record_metrics(
    *,
    total_ms: int,
    retrieve_ms: int,
    rule_ms: int,
    cache_lookup_ms: int,
    upstream_ms: int,
    cache_hit: bool,
) -> None:
    with _stats_lock:
        _recent_metrics.append(
            {
                "total_ms": float(total_ms),
                "retrieve_ms": float(retrieve_ms),
                "rule_ms": float(rule_ms),
                "cache_lookup_ms": float(cache_lookup_ms),
                "upstream_ms": float(upstream_ms),
                "cache_hit": cache_hit,
            }
        )
        if len(_recent_metrics) > _MAX_STATS:
            _recent_metrics[:] = _recent_metrics[-_MAX_STATS:]


def _compute_stats() -> StatsResponse:
    with _stats_lock:
        metrics = list(_recent_metrics)
    times = [int(item["total_ms"]) for item in metrics]
    n = len(times)
    if n == 0:
        return StatsResponse(
            recent_count=0,
            recent_avg_ms=0,
            recent_p50_ms=0,
            recent_p95_ms=0,
            recent_max_ms=0,
            recent_avg_upstream_ms=0,
            recent_p95_upstream_ms=0,
            recent_cached_count=0,
            recent_cache_hit_rate=0,
        )
    times.sort()
    upstream_times = sorted(int(item["upstream_ms"]) for item in metrics)
    cached_count = sum(1 for item in metrics if bool(item["cache_hit"]))
    return StatsResponse(
        recent_count=n,
        recent_avg_ms=round(sum(times) / n, 1),
        recent_p50_ms=float(times[n // 2]),
        recent_p95_ms=float(times[min(n - 1, int(n * 0.95))]),
        recent_max_ms=float(times[-1]),
        recent_avg_upstream_ms=round(sum(upstream_times) / n, 1),
        recent_p95_upstream_ms=float(upstream_times[min(n - 1, int(n * 0.95))]),
        recent_cached_count=cached_count,
        recent_cache_hit_rate=round((cached_count / n) * 100, 1),
    )


@router.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """实验室安全问答主入口：本独立项目固定走 lab / Dify RAG 链路。"""
    t0 = time.perf_counter()
    mode = "lab"
    question = payload.question.strip()
    session = get_or_create(payload.session_id)
    timings = {
        "retrieve_ms": 0,
        "rule_ms": 0,
        "cache_lookup_ms": 0,
        "upstream_ms": 0,
        "cache_hit": False,
    }

    t_retrieve = time.perf_counter()
    citations = retrieve_citations(question, top_k=DEFAULT_TOP_K)
    timings["retrieve_ms"] = round((time.perf_counter() - t_retrieve) * 1000)

    t_rule = time.perf_counter()
    rule = match_rule(question)
    timings["rule_ms"] = round((time.perf_counter() - t_rule) * 1000)
    if should_force_more_info(question, rule):
        rule = {
            "id": str((rule or {}).get("id") or "R-ASK-LOCAL"),
            "action": "ask_for_more_info",
            "severity": str((rule or {}).get("severity") or "low"),
            "response": "当前问题缺少关键对象或场景信息，我需要先确认具体条件后才能给出安全建议。",
        }
    rule_action = str((rule or {}).get("action") or "")
    decision = "dify_answer"
    followup_logged = False

    if rule and should_enforce_terminal_rule(question, rule):
        decision = (
            "rule_blocked" if rule_action == "refuse"
            else "emergency_redirect" if rule_action == "redirect_emergency"
            else "rule_direct_answer" if rule_action == "direct_safe_answer"
            else "need_more_info"
        )
        answer = build_rule_answer(rule, citations)
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        _record_metrics(total_ms=elapsed_ms, **timings)
        add_history(session.session_id, question, answer)
        record_kb_usage(_extract_kb_ids(citations))
        return ChatResponse(
            answer=answer,
            mode=mode,
            model="rule-engine",
            decision=decision,
            risk_level=str((rule or {}).get("severity") or ""),
            matched_rule_id=str((rule or {}).get("id") or ""),
            matched_rule_action=rule_action,
            elapsed_ms=elapsed_ms,
            session_id=session.session_id,
            citations=citations,
            timings={"total_ms": elapsed_ms, **timings},
        )

    low_confidence, low_reason = assess_low_confidence(citations)
    if low_confidence:
        decision = "dify_low_confidence"

    model = "dify-workflow"
    fast_path_citations = select_fast_path_citations(
        question=question,
        citations=citations,
        low_confidence=low_confidence,
        rule=rule,
        session_has_history=bool(session.history),
        history=session.history,
    )
    if fast_path_citations:
        citations = fast_path_citations
        answer = build_fast_path_answer(question, citations)
        set_cached_answer(question, {"answer": answer, "model": "local-fast-path", "citations": [item.model_dump() if hasattr(item, "model_dump") else item for item in citations]})
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        _record_metrics(total_ms=elapsed_ms, **timings)
        add_history(session.session_id, question, answer)
        record_kb_usage(_extract_kb_ids(citations))
        return ChatResponse(
            answer=answer,
            mode=mode,
            model="local-fast-path",
            decision="dify_answer",
            risk_level="",
            matched_rule_id="",
            matched_rule_action="",
            low_confidence=False,
            low_confidence_reason="",
            followup_logged=False,
            elapsed_ms=elapsed_ms,
            session_id=session.session_id,
            citations=citations,
            timings={"total_ms": elapsed_ms, **timings},
        )

    # ``/api/chat`` is the user-facing complete-response endpoint.  Waiting for
    # a remote LLM to finish streaming makes its P95 equal to the model's token
    # generation duration (previously about 6.5 s), even though a complete,
    # cited safety answer is already available in the curated local KB.  Finish
    # on the local path by default; an operator may explicitly set
    # LABSAFE_RESPONSE_MODE=dify when a generative answer is preferred over the
    # complete-response latency SLO.
    if use_local_complete_response():
        if citations:
            answer = build_fast_path_answer(question, citations)
            model = "local-kb-complete"
            decision = "local_complete_low_confidence" if low_confidence else "local_complete_answer"
        else:
            # No rule matched AND no KB citations => out-of-scope.
            # build_fallback_lab_answer now returns the OOS template; we tag
            # the decision explicitly so logs and metrics can distinguish
            # "made up a safety answer" from "polite decline".
            if rule is None:
                decision = "out_of_scope_local"
            else:
                decision = "local_complete_low_confidence"
            answer = build_fallback_lab_answer(
                question=question,
                citations=citations,
                rule=rule,
                low_confidence_reason=low_reason or "no_kb_match",
            )
            model = "local-kb-conservative"
        if low_confidence:
            followup_logged = append_low_confidence_followup(
                question=question,
                mode=mode,
                decision=decision,
                risk_level=str((rule or {}).get("severity") or ""),
                matched_rule_id=str((rule or {}).get("id") or ""),
                matched_rule_action=rule_action,
                low_confidence_reason=low_reason,
                citations=citations,
            )
            if followup_logged:
                answer = append_low_confidence_followup_notice(answer)
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        _record_metrics(total_ms=elapsed_ms, **timings)
        add_history(session.session_id, question, answer)
        record_kb_usage(_extract_kb_ids(citations))
        return ChatResponse(
            answer=answer,
            mode=mode,
            model=model,
            decision=decision,
            risk_level=str((rule or {}).get("severity") or ""),
            matched_rule_id=str((rule or {}).get("id") or ""),
            matched_rule_action=rule_action,
            low_confidence=low_confidence,
            low_confidence_reason=low_reason,
            followup_logged=followup_logged,
            elapsed_ms=elapsed_ms,
            session_id=session.session_id,
            citations=citations,
            timings={"total_ms": elapsed_ms, **timings},
        )

    use_cache = not low_confidence and not rule and not session.history
    effective_question = question
    if session.history and not session.conversation_id:
        effective_question = _build_contextual_query(question, session.history)
    if use_cache:
        t_cache = time.perf_counter()
        cached = get_cached_answer(question)
        timings["cache_lookup_ms"] = round((time.perf_counter() - t_cache) * 1000)
        if cached:
            timings["cache_hit"] = True
            answer = str(cached.get("answer") or "")
            model = str(cached.get("model") or "dify-workflow")
            cached_citations = cached.get("citations") or []
            if isinstance(cached_citations, list) and cached_citations:
                citations = cached_citations
            cache_truncated = looks_truncated(answer) if model == "dify-workflow" else False
            if cache_truncated:
                answer = append_truncation_notice(answer)
            elapsed_ms = round((time.perf_counter() - t0) * 1000)
            _record_metrics(total_ms=elapsed_ms, **timings)
            add_history(session.session_id, question, answer)
            record_kb_usage(_extract_kb_ids(citations))
            return ChatResponse(
                answer=answer or "No answer returned.",
                mode=mode,
                model=model,
                decision="dify_answer",
                risk_level="",
                matched_rule_id="",
                matched_rule_action="",
                low_confidence=False,
                low_confidence_reason="",
                answer_possibly_truncated=cache_truncated,
                followup_logged=False,
                elapsed_ms=elapsed_ms,
                session_id=session.session_id,
                citations=citations,
                timings={"total_ms": elapsed_ms, **timings},
            )

    try:
        t_upstream = time.perf_counter()
        answer, model, returned_conversation_id = call_dify_lab(
            effective_question,
            conversation_id=session.conversation_id,
        )
        timings["upstream_ms"] = round((time.perf_counter() - t_upstream) * 1000)
        if returned_conversation_id:
            set_conversation_id(session.session_id, returned_conversation_id)
        if rule:
            decision = "dify_answer_guarded"
        if use_cache and answer:
            set_cached_answer(
                question,
                {
                    "answer": answer,
                    "model": model,
                    "citations": [item.model_dump() if hasattr(item, "model_dump") else item for item in citations],
                },
            )
    except HTTPException as exc:
        # 记录失败耗时（time-to-failure）——此前异常路径不给 upstream_ms 赋值，
        # 结果 upstream_ms 停在 0，误导性地看起来像“上游从未被调用”。
        timings["upstream_ms"] = round((time.perf_counter() - t_upstream) * 1000)
        # Out-of-scope gets a dedicated decision tag so analytics and
        # operator dashboards can filter "questions we should not have
        # answered" vs "Dify broke" cleanly.
        if rule is None and not citations:
            decision = "out_of_scope_fallback"
        else:
            decision = "structured_fallback"
        detail = str(getattr(exc, "detail", "") or "")
        fallback_reason = _classify_dify_failure(detail)
        logger.warning(
            "dify upstream failed after %sms, using structured fallback (%s): %s",
            timings["upstream_ms"], fallback_reason, detail,
        )
        answer = build_fallback_lab_answer(
            question=question,
            citations=citations,
            rule=rule,
            low_confidence_reason=low_reason or fallback_reason,
        )
        model = "fallback-rule-engine"

    answer_possibly_truncated = looks_truncated(answer) if model == "dify-workflow" else False
    if answer_possibly_truncated:
        answer = append_truncation_notice(answer)

    if low_confidence:
        followup_logged = append_low_confidence_followup(
            question=question,
            mode=mode,
            decision=decision,
            risk_level=str((rule or {}).get("severity") or ""),
            matched_rule_id=str((rule or {}).get("id") or ""),
            matched_rule_action=rule_action,
            low_confidence_reason=low_reason,
            citations=citations,
        )
        if followup_logged:
            answer = append_low_confidence_followup_notice(answer)

    elapsed_ms = round((time.perf_counter() - t0) * 1000)
    _record_metrics(total_ms=elapsed_ms, **timings)
    add_history(session.session_id, question, answer)
    record_kb_usage(_extract_kb_ids(citations))

    return ChatResponse(
        answer=answer or "No answer returned.",
        mode=mode,
        model=model,
        decision=decision,
        risk_level=str((rule or {}).get("severity") or ""),
        matched_rule_id=str((rule or {}).get("id") or ""),
        matched_rule_action=rule_action,
        low_confidence=low_confidence,
        low_confidence_reason=low_reason,
        answer_possibly_truncated=answer_possibly_truncated,
        followup_logged=followup_logged,
        elapsed_ms=elapsed_ms,
        session_id=session.session_id,
        citations=citations,
        timings={"total_ms": elapsed_ms, **timings},
    )


@router.get("/api/search")
def search(q: str, top_k: int = 5) -> dict[str, Any]:
    query = (q or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="q is required.")
    top_k = max(1, min(10, int(top_k)))
    citations = retrieve_citations(query, top_k=top_k)
    return {"query": query, "count": len(citations), "citations": [item.model_dump() for item in citations]}


@router.get("/v1/parameters")
def dify_parameters_proxy(request: Request) -> Response:
    endpoint = f"{resolve_dify_api_base()}/parameters"
    headers: dict[str, str] = {}
    auth = build_dify_proxy_auth(request)
    if auth:
        headers["Authorization"] = auth
    try:
        upstream = requests.get(endpoint, headers=headers, timeout=(8, 20))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"dify_proxy_request_failed: {exc}") from exc
    try:
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("Content-Type", "application/json"),
        )
    finally:
        upstream.close()


@router.post("/v1/chat-messages")
async def dify_chat_messages_proxy(request: Request) -> Response:
    endpoint = f"{resolve_dify_api_base()}/chat-messages"
    timeout = float(os.getenv("DIFY_TIMEOUT", str(DIFY_DEFAULT_TIMEOUT)) or str(DIFY_DEFAULT_TIMEOUT))
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid_json_body: {exc}") from exc

    headers = {"Content-Type": "application/json"}
    auth = build_dify_proxy_auth(request)
    if auth:
        headers["Authorization"] = auth

    try:
        upstream = await run_in_threadpool(
            requests.post,
            endpoint,
            headers=headers,
            json=payload,
            timeout=(20, timeout),
            stream=True,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"dify_proxy_request_failed: {exc}") from exc

    content_type = str(upstream.headers.get("Content-Type", "") or "").lower()
    if "text/event-stream" in content_type:
        def _iter_sse():
            try:
                for chunk in upstream.iter_content(chunk_size=_dify_sse_chunk_size()):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()
        return StreamingResponse(
            _iter_sse(),
            status_code=upstream.status_code,
            media_type="text/event-stream",
            headers=_dify_sse_response_headers(),
        )

    body = upstream.content
    status_code = upstream.status_code
    media_type = upstream.headers.get("Content-Type", "application/json")
    upstream.close()
    return Response(content=body, status_code=status_code, media_type=media_type)


@router.get("/api/stats", response_model=StatsResponse)
def performance_stats() -> StatsResponse:
    return _compute_stats()


@router.post("/api/feedback")
def submit_feedback(payload: FeedbackRequest) -> dict[str, str]:
    rating = (payload.rating or "").strip()
    if rating not in ("useful", "not_useful"):
        raise HTTPException(status_code=400, detail="rating must be 'useful' or 'not_useful'")
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "session_id": (payload.session_id or "")[:128],
        "question": (payload.question or "").strip()[:_FEEDBACK_MAX_QUESTION],
        "answer": (payload.answer or "")[:500],
        "rating": rating,
        "comment": (payload.comment or "").strip()[:_FEEDBACK_MAX_COMMENT],
    }
    with _FEEDBACK_LOCK:
        file_exists = FEEDBACK_FILE.exists()
        with FEEDBACK_FILE.open("a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FEEDBACK_HEADERS, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    return {"status": "ok"}
