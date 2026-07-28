from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..models import DemoMetaResponse
from ..repositories import get_kb_entries
from ..services import get_demo_meta
from ..services.auth_service import verify_password
from ..services.upstream_service import resolve_dify_api_base

import os
import requests
import time

router = APIRouter()

_DIFY_HEALTH_CACHE: dict[str, object] = {
    "checked_at": 0.0,
    "reachable": False,
    "error": "",
}


def _get_dify_probe_cache_seconds() -> int:
    try:
        return max(0, int(os.getenv("DIFY_HEALTH_CACHE_SECONDS", "15") or "15"))
    except ValueError:
        return 15


def _probe_dify_reachable(dify_base: str) -> tuple[bool, str, bool]:
    cache_seconds = _get_dify_probe_cache_seconds()
    now = time.monotonic()
    checked_at = float(_DIFY_HEALTH_CACHE.get("checked_at") or 0)
    if cache_seconds > 0 and now - checked_at < cache_seconds:
        return (
            bool(_DIFY_HEALTH_CACHE.get("reachable")),
            str(_DIFY_HEALTH_CACHE.get("error") or ""),
            True,
        )

    dify_reachable = False
    dify_error = ""
    app_key = os.getenv("DIFY_APP_API_KEY", "").strip()
    if not app_key:
        dify_error = "dify_app_key_missing"
        _DIFY_HEALTH_CACHE.update({
            "checked_at": now,
            "reachable": False,
            "error": dify_error,
        })
        return False, dify_error, False

    upstream_probe = f"{dify_base.rstrip('/')}/parameters"
    response = None
    try:
        response = requests.get(
            upstream_probe,
            headers={"Authorization": f"Bearer {app_key}"},
            timeout=(1, 2),
        )
        dify_reachable = 200 <= response.status_code < 300
        if not dify_reachable:
            dify_error = f"dify_http_{response.status_code}"
    except requests.RequestException as exc:
        dify_error = str(exc)
    finally:
        if response is not None:
            response.close()

    _DIFY_HEALTH_CACHE.update({
        "checked_at": now,
        "reachable": dify_reachable,
        "error": dify_error,
    })
    return dify_reachable, dify_error, False


@router.get("/health")
def health() -> dict[str, object]:
    try:
        dify_base = resolve_dify_api_base()
        dify_base_error = ""
    except HTTPException as exc:
        dify_base = ""
        dify_base_error = str(exc.detail)
    dify_reachable, dify_error, dify_probe_cached = (
        _probe_dify_reachable(dify_base) if dify_base else (False, dify_base_error, False)
    )

    return {
        "ok": True,
        "status": "ok" if dify_reachable else "degraded",
        "service": "lab-safe-assistant",
        "kb_loaded": len(get_kb_entries()),
        "dify_base_url": dify_base,
        "dify_app_key_configured": bool(os.getenv("DIFY_APP_API_KEY", "").strip()),
        "dify_reachable": dify_reachable,
        "dify_error": dify_error,
        "dify_probe_cached": dify_probe_cached,
    }


@router.get(
    "/api/auth/check",
    dependencies=[Depends(verify_password)],
)
def auth_check() -> dict[str, bool]:
    """Validate the demo password without exposing application data."""
    return {"ok": True}


@router.get(
    "/api/meta",
    response_model=DemoMetaResponse,
    dependencies=[Depends(verify_password)],
)
def demo_meta() -> DemoMetaResponse:
    return get_demo_meta()
