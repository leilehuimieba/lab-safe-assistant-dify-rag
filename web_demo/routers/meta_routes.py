from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models import DemoMetaResponse
from ..repositories import get_kb_entries
from ..services import get_demo_meta
from ..services.auth_service import verify_password
from ..services.upstream_service import resolve_dify_api_base

import os
import requests

router = APIRouter(dependencies=[Depends(verify_password)])


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
