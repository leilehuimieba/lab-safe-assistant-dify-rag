from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from web_demo.models import ChatRequest, Citation


def test_local_complete_mode_is_enabled_by_default(monkeypatch):
    """The latency-critical endpoint must not wait for a generative stream by default."""
    monkeypatch.delenv("LABSAFE_RESPONSE_MODE", raising=False)

    from web_demo.services.response_mode_service import use_local_complete_response

    assert use_local_complete_response() is True


def test_dify_mode_can_be_explicitly_selected(monkeypatch):
    monkeypatch.setenv("LABSAFE_RESPONSE_MODE", "dify")

    from web_demo.services.response_mode_service import use_local_complete_response

    assert use_local_complete_response() is False


def test_chat_returns_complete_local_kb_answer_without_waiting_for_dify(monkeypatch):
    """A normal high-confidence request must return its complete answer locally.

    This keeps complete-response latency independent of Dify's token-generation
    duration; Dify remains available when an operator explicitly selects its
    richer mode.
    """
    monkeypatch.setenv("LABSAFE_RESPONSE_MODE", "local_complete")

    from web_demo.routers import chat_routes

    citation = Citation(
        kb_id="KB-TEST-001",
        title="测试安全条目",
        source_title="测试来源",
        source_org="测试机构",
        source_url="https://example.test/safety",
        risk_level="3",
        snippet="佩戴防护用品并按书面 SOP 操作。",
        score=9.0,
    )
    session = SimpleNamespace(session_id="test-session", history=[], conversation_id="")

    with (
        patch.object(chat_routes, "retrieve_citations", return_value=[citation]),
        patch.object(chat_routes, "match_rule", return_value=None),
        patch.object(chat_routes, "get_or_create", return_value=session),
        patch.object(chat_routes, "select_fast_path_citations", return_value=[]),
        patch.object(chat_routes, "call_dify_lab", side_effect=AssertionError("Dify must not be awaited")),
        patch.object(chat_routes, "add_history"),
        patch.object(chat_routes, "record_kb_usage"),
    ):
        response = chat_routes.chat(ChatRequest(question="这个场景的安全要求是什么？"))

    assert response.model == "local-kb-complete"
    assert response.decision == "local_complete_answer"
    assert "结论:" in response.answer
    assert "步骤:" in response.answer
    assert "禁止事项:" in response.answer
    assert response.timings.upstream_ms == 0
