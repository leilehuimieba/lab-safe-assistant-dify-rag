from __future__ import annotations

import os

from ..models import DemoMetaResponse
from ..repositories import (
    APP_VERSION,
    FORMAL_EVAL_SCORE,
    STABILITY_EVIDENCE,
    KB_CHUNK_IMPORT_COUNT,
    KB_EXTERNAL_IMPORT_COUNT,
    KB_IMPORT_SUCCESS_COUNT,
    get_kb_entries,
)
from .upstream_service import resolve_dify_api_base


def _safe_dify_base_url() -> str:
    # /api/meta 只是回显配置，不应因白名单校验失败而 500。
    try:
        return resolve_dify_api_base()
    except Exception as exc:
        return f"(invalid: {exc})"


def get_demo_meta() -> DemoMetaResponse:
    dify_app_key = os.getenv("DIFY_APP_API_KEY", "").strip()
    return DemoMetaResponse(
        app_version=APP_VERSION,
        chat_lane_lab="Dify RAG 正式问答链路" if dify_app_key else "Dify 未配置，当前处于结构化回退模式",
        acceptance_status="project-1-extracted",
        formal_eval_score=FORMAL_EVAL_SCORE,
        stability_status=STABILITY_EVIDENCE,
        knowledge_base_rows=len(get_kb_entries()),
        knowledge_base_imported=KB_IMPORT_SUCCESS_COUNT,
        knowledge_base_chunked=KB_CHUNK_IMPORT_COUNT,
        knowledge_base_external=KB_EXTERNAL_IMPORT_COUNT,
        demo_port=os.getenv("DEMO_PORT", "8088").strip() or "8088",
        dify_base_url=_safe_dify_base_url(),
        dify_app_key_configured=bool(dify_app_key),
    )
