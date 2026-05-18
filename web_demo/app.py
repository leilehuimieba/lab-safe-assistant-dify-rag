from __future__ import annotations

from fastapi import FastAPI
from .routers import chat_router, meta_router

app = FastAPI(title="Lab Safety Assistant - Dify RAG Project")
app.include_router(meta_router)
app.include_router(chat_router)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None
