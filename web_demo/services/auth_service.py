from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request

_HEADER_KEY = "x-password"


def _get_password_from_request(request: Request) -> str:
    """从请求头或查询参数中提取密码。"""
    pw = request.headers.get(_HEADER_KEY, "").strip()
    if pw:
        return pw
    return (request.query_params.get("password") or "").strip()


def verify_password(request: Request) -> None:
    """FastAPI Depends 依赖：验证请求中的密码是否匹配环境变量。"""
    demo_password = os.getenv("DEMO_PASSWORD", "").strip()
    if not demo_password:
        raise HTTPException(
            status_code=503,
            detail="demo authentication is not configured",
        )
    provided = _get_password_from_request(request)
    if provided != demo_password:
        raise HTTPException(status_code=401, detail="unauthorized: invalid password")
