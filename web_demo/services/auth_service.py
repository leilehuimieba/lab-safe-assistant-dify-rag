from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request, Depends

_DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "").strip()

_HEADER_KEY = "x-password"


def _get_password_from_request(request: Request) -> str:
    """从请求头或查询参数中提取密码。"""
    pw = request.headers.get(_HEADER_KEY, "").strip()
    if pw:
        return pw
    return (request.query_params.get("password") or "").strip()


def verify_password(request: Request) -> None:
    """FastAPI Depends 依赖：验证请求中的密码是否匹配环境变量。"""
    if not _DEMO_PASSWORD:
        # 未配置密码时不做验证（向后兼容）
        return
    provided = _get_password_from_request(request)
    if provided != _DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized: invalid password")
