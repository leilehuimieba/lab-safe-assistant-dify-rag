from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .routers import chat_router, meta_router

# Windows 上 mimetypes 可能把 .js 识别为 text/plain，需手动修正
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")

app = FastAPI(title="Lab Safety Assistant - Dify RAG Project")
app.include_router(meta_router)
app.include_router(chat_router)

# 托管前端 React SPA 构建产物
_frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"
_frontend_index = _frontend_dist / "index.html"

if _frontend_index.exists():
    # 自定义 /assets/* 路由，确保 MIME 类型正确
    @app.get("/assets/{path:path}")
    async def serve_asset(path: str) -> FileResponse:
        file_path = _frontend_dist / "assets" / path
        # 防止目录遍历
        try:
            file_path.resolve().relative_to(_frontend_dist.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Forbidden")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Not found")
        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    @app.get("/favicon.svg")
    async def serve_favicon() -> FileResponse:
        favicon = _frontend_dist / "favicon.svg"
        if favicon.exists():
            return FileResponse(favicon, media_type="image/svg+xml")
        raise HTTPException(status_code=404)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None
