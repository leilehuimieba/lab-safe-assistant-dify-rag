from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..models import DemoMetaResponse
from ..repositories import HTML_FILE
from ..services import get_demo_meta

router = APIRouter()

# 若前端已构建，优先返回 React SPA；否则回退到旧模板
_FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "dist" / "index.html"

@router.get("/")
def index() -> FileResponse:
    if _FRONTEND_INDEX.exists():
        return FileResponse(_FRONTEND_INDEX)
    return FileResponse(HTML_FILE)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/meta", response_model=DemoMetaResponse)
def demo_meta() -> DemoMetaResponse:
    return get_demo_meta()
