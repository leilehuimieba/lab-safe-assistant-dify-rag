from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest


RENDERER_ROOT = (
    Path.home()
    / ".codex"
    / "plugins"
    / "cache"
    / "openai-primary-runtime"
    / "documents"
)
RENDERER_CANDIDATES = sorted(RENDERER_ROOT.glob("*/skills/documents/render_docx.py"))
RENDERER_PATH = RENDERER_CANDIDATES[-1] if RENDERER_CANDIDATES else None


def _load_renderer_module():
    assert RENDERER_PATH is not None
    pdf2image_stub = types.ModuleType("pdf2image")
    pdf2image_stub.convert_from_path = lambda *args, **kwargs: []
    pdf2image_stub.pdfinfo_from_path = lambda *args, **kwargs: {}
    sys.modules["pdf2image"] = pdf2image_stub
    spec = importlib.util.spec_from_file_location("codex_render_docx", RENDERER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(
    os.name != "nt" or RENDERER_PATH is None,
    reason="Windows Codex document renderer is not installed",
)
def test_user_installation_uri_is_a_valid_windows_file_uri(tmp_path: Path) -> None:
    renderer = _load_renderer_module()
    helper = getattr(renderer, "_user_installation_uri", None)

    assert helper is not None, "renderer must expose a normalized profile URI helper"
    uri = helper(str(tmp_path / "profile"))

    assert uri.startswith("file:///")
    assert "\\" not in uri
    assert ":/" in uri


@pytest.mark.skipif(
    os.name != "nt" or RENDERER_PATH is None,
    reason="Windows Codex document renderer is not installed",
)
def test_renderer_finds_the_bundled_poppler_executables() -> None:
    renderer = _load_renderer_module()
    helper = getattr(renderer, "_bundled_poppler_path", None)

    assert helper is not None, "renderer must expose a bundled Poppler locator"
    poppler_path = helper()

    assert poppler_path is not None
    poppler_bin = Path(poppler_path)
    assert (poppler_bin / "pdfinfo.exe").is_file()
    assert (poppler_bin / "pdftoppm.exe").is_file()
