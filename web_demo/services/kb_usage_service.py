from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_USAGE_LOCK = threading.Lock()
_CALLED_KB_IDS: set[str] = set()
_CALL_COUNTS: dict[str, int] = {}

_USAGE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"
_USAGE_FILE = _USAGE_DIR / "kb_usage.json"


def record_kb_usage(kb_ids: list[str]) -> None:
    if not kb_ids:
        return
    with _USAGE_LOCK:
        for kb_id in kb_ids:
            _CALLED_KB_IDS.add(kb_id)
            _CALL_COUNTS[kb_id] = _CALL_COUNTS.get(kb_id, 0) + 1
        _persist_usage()


def get_called_kb_ids() -> set[str]:
    with _USAGE_LOCK:
        return set(_CALLED_KB_IDS)


def get_call_counts() -> dict[str, int]:
    with _USAGE_LOCK:
        return dict(_CALL_COUNTS)


def is_kb_called(kb_id: str) -> bool:
    with _USAGE_LOCK:
        return kb_id in _CALLED_KB_IDS


def get_kb_call_count(kb_id: str) -> int:
    with _USAGE_LOCK:
        return _CALL_COUNTS.get(kb_id, 0)


def _persist_usage() -> None:
    _USAGE_DIR.mkdir(parents=True, exist_ok=True)
    data = {"called_ids": list(_CALLED_KB_IDS), "call_counts": _CALL_COUNTS}
    try:
        tmp = _USAGE_FILE.with_suffix(_USAGE_FILE.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, _USAGE_FILE)
    except OSError:
        pass


def load_usage_from_disk() -> int:
    if not _USAGE_FILE.exists():
        return 0
    try:
        with open(_USAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return 0
    called_ids = data.get("called_ids", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    call_counts = data.get("call_counts", {}) if isinstance(data, dict) else {}
    with _USAGE_LOCK:
        _CALLED_KB_IDS.update(called_ids)
        _CALL_COUNTS.update(call_counts)
    return len(_CALLED_KB_IDS)


def get_usage_stats() -> dict[str, Any]:
    with _USAGE_LOCK:
        return {
            "called_count": len(_CALLED_KB_IDS),
            "total_calls": sum(_CALL_COUNTS.values()),
        }
