from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..models import DemoMetaResponse
from ..repositories import HTML_FILE, get_kb_entries
from ..services import get_demo_meta
from ..services.upstream_service import resolve_dify_api_base

import os
import requests

router = APIRouter()

# 若前端已构建，优先返回 React SPA；否则回退到旧模板
_FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "dist" / "index.html"

@router.get("/")
def index() -> FileResponse:
    if _FRONTEND_INDEX.exists():
        return FileResponse(_FRONTEND_INDEX)
    return FileResponse(HTML_FILE)


@router.get("/health")
def health() -> dict[str, object]:
    dify_reachable = False
    dify_error = ""
    dify_base = resolve_dify_api_base()
    upstream_probe = dify_base[:-3] if dify_base.endswith("/v1") else dify_base
    try:
        response = requests.get(upstream_probe, timeout=(2, 3))
        dify_reachable = 200 <= response.status_code < 500
    except requests.RequestException as exc:
        dify_error = str(exc)

    return {
        "ok": True,
        "status": "ok",
        "service": "lab-safe-assistant",
        "kb_loaded": len(get_kb_entries()),
        "dify_base_url": dify_base,
        "dify_app_key_configured": bool(os.getenv("DIFY_APP_API_KEY", "").strip()),
        "dify_reachable": dify_reachable,
        "dify_error": dify_error,
    }


@router.get("/api/meta", response_model=DemoMetaResponse)
def demo_meta() -> DemoMetaResponse:
    return get_demo_meta()
