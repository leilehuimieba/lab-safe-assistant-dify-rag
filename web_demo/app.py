from __future__ import annotations

import atexit
import logging
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .routers import chat_router, meta_router, kb_router
from .repositories import get_kb_entries
from .services.response_cache_service import load_cache_from_disk, save_cache_to_disk
from .services.kb_usage_service import load_usage_from_disk

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    kb = get_kb_entries()
    logger.info("KB preloaded: %d entries", len(kb))
    loaded = load_cache_from_disk()
    logger.info("Cache loaded from disk: %d entries", loaded)
    usage_loaded = load_usage_from_disk()
    logger.info("KB usage loaded from disk: %d entries", usage_loaded)
    atexit.register(save_cache_to_disk)
    yield
    saved = save_cache_to_disk()
    logger.info("Cache saved to disk: %d entries", saved)


# Windows 上 mimetypes 可能把 .js 识别为 text/plain，需手动修正
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")

app = FastAPI(title="Lab Safety Assistant - Dify RAG Project", lifespan=lifespan)
app.include_router(meta_router)
app.include_router(kb_router)
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
