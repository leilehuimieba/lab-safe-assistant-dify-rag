from __future__ import annotations

import csv
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from ..models import ChatRequest, ChatResponse, FeedbackRequest, StatsResponse
from ..repositories import DEFAULT_TOP_K, DIFY_DEFAULT_TIMEOUT, REPO_ROOT
from ..services import (
    retrieve_citations, match_rule, should_enforce_terminal_rule,
    build_rule_answer, assess_low_confidence, append_low_confidence_followup,
    append_low_confidence_followup_notice, call_dify_lab,
    build_fallback_lab_answer, resolve_dify_api_base, build_dify_proxy_auth,
    get_or_create, set_conversation_id, add_history,
)

router = APIRouter()

# --- In-memory performance stats ---
_stats_lock = threading.Lock()
_recent_times: list[int] = []  # last 200 elapsed_ms
_MAX_STATS = 200

FEEDBACK_FILE = REPO_ROOT / "artifacts" / "user_feedback" / "feedback.csv"
FEEDBACK_HEADERS = ["created_at", "session_id", "question", "answer", "rating", "comment"]


def _record_time(elapsed_ms: int) -> None:
    with _stats_lock:
        _recent_times.append(elapsed_ms)
        if len(_recent_times) > _MAX_STATS:
            _recent_times[:] = _recent_times[-_MAX_STATS:]


def _compute_stats() -> StatsResponse:
    with _stats_lock:
        times = list(_recent_times)
    n = len(times)
    if n == 0:
        return StatsResponse(recent_count=0, recent_avg_ms=0, recent_p50_ms=0, recent_p95_ms=0, recent_max_ms=0)
    times.sort()
    return StatsResponse(
        recent_count=n,
        recent_avg_ms=round(sum(times) / n, 1),
        recent_p50_ms=float(times[n // 2]),
        recent_p95_ms=float(times[min(n - 1, int(n * 0.95))]),
        recent_max_ms=float(times[-1]),
    )


@router.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """实验室安全问答主入口：本独立项目固定走 lab / Dify RAG 链路。"""
    t0 = time.perf_counter()
    mode = "lab"
    question = payload.question.strip()
    session = get_or_create(payload.session_id)
    citations = retrieve_citations(question, top_k=DEFAULT_TOP_K)
    rule = match_rule(question)
    rule_action = str((rule or {}).get("action") or "")
    decision = "dify_answer"
    followup_logged = False

    if rule and should_enforce_terminal_rule(question, rule):
        decision = (
            "rule_blocked" if rule_action == "refuse"
            else "emergency_redirect" if rule_action == "redirect_emergency"
            else "need_more_info"
        )
        answer = build_rule_answer(rule, citations)
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        _record_time(elapsed_ms)
        add_history(session.session_id, question, answer)
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
        )

    low_confidence, low_reason = assess_low_confidence(citations)
    if low_confidence:
        decision = "dify_low_confidence"

    model = "dify-workflow"
    try:
        answer, model, returned_conversation_id = call_dify_lab(
            question,
            conversation_id=session.conversation_id,
        )
        if returned_conversation_id:
            set_conversation_id(session.session_id, returned_conversation_id)
        if rule:
            decision = "dify_answer_guarded"
    except HTTPException:
        decision = "structured_fallback"
        answer = build_fallback_lab_answer(question=question, citations=citations, rule=rule, low_confidence_reason=low_reason)
        model = "fallback-rule-engine"

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
    _record_time(elapsed_ms)
    add_history(session.session_id, question, answer)

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
        followup_logged=followup_logged,
        elapsed_ms=elapsed_ms,
        session_id=session.session_id,
        citations=citations,
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
    return Response(content=upstream.content, status_code=upstream.status_code, media_type=upstream.headers.get("Content-Type", "application/json"))


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
        upstream = requests.post(endpoint, headers=headers, json=payload, timeout=(20, timeout), stream=True)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"dify_proxy_request_failed: {exc}") from exc

    content_type = str(upstream.headers.get("Content-Type", "") or "").lower()
    if "text/event-stream" in content_type:
        def _iter_sse():
            try:
                for chunk in upstream.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()
        return StreamingResponse(_iter_sse(), status_code=upstream.status_code, media_type="text/event-stream")

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
        "session_id": payload.session_id,
        "question": (payload.question or "").strip(),
        "answer": (payload.answer or "")[:500],
        "rating": rating,
        "comment": (payload.comment or "").strip(),
    }
    file_exists = FEEDBACK_FILE.exists()
    with FEEDBACK_FILE.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FEEDBACK_HEADERS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return {"status": "ok"}
