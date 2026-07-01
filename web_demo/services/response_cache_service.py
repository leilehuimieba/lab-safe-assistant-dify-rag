from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from ..repositories import normalize_search_text


@dataclass
class CacheEntry:
    created_at: float
    payload: dict[str, Any]


_LOCK = threading.Lock()
_CACHE: dict[str, CacheEntry] = {}

_DEFAULT_TTL_SECONDS = int(os.getenv("ANSWER_CACHE_TTL_SECONDS", "21600") or "21600")
_DEFAULT_MAX_ITEMS = int(os.getenv("ANSWER_CACHE_MAX_ITEMS", "1000") or "1000")

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"
_CACHE_FILE = _CACHE_DIR / "response_cache.json"


def _cache_key(question: str) -> str:
    return normalize_search_text(question)


def _purge_expired(now: float, ttl_seconds: int) -> None:
    expired = [key for key, entry in _CACHE.items() if now - entry.created_at > ttl_seconds]
    for key in expired:
        _CACHE.pop(key, None)


def get_cached_answer(question: str) -> dict[str, Any] | None:
    key = _cache_key(question)
    if not key:
        return None
    ttl_seconds = max(60, _DEFAULT_TTL_SECONDS)
    now = time.time()
    with _LOCK:
        _purge_expired(now, ttl_seconds)
        entry = _CACHE.get(key)
        if not entry:
            return None
        return dict(entry.payload)


def set_cached_answer(question: str, payload: dict[str, Any]) -> None:
    key = _cache_key(question)
    if not key:
        return
    now = time.time()
    max_items = max(10, _DEFAULT_MAX_ITEMS)
    with _LOCK:
        _purge_expired(now, max(60, _DEFAULT_TTL_SECONDS))
        _CACHE[key] = CacheEntry(created_at=now, payload=dict(payload))
        if len(_CACHE) > max_items:
            overflow = len(_CACHE) - max_items
            for stale_key, _ in sorted(_CACHE.items(), key=lambda item: item[1].created_at)[:overflow]:
                _CACHE.pop(stale_key, None)


def load_cache_from_disk() -> int:
    """Load persisted cache from disk. Returns number of entries loaded."""
    if not _CACHE_FILE.exists():
        return 0
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return 0
    now = time.time()
    ttl = max(60, _DEFAULT_TTL_SECONDS)
    loaded = 0
    with _LOCK:
        for key, entry_data in data.items():
            created_at = entry_data.get("created_at", 0)
            if now - created_at > ttl:
                continue
            _CACHE[key] = CacheEntry(created_at=created_at, payload=entry_data.get("payload", {}))
            loaded += 1
    return loaded


def save_cache_to_disk() -> int:
    """Persist current cache to disk. Returns number of entries saved."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    now = time.time()
    ttl = max(60, _DEFAULT_TTL_SECONDS)
    with _LOCK:
        _purge_expired(now, ttl)
        data = {key: {"created_at": entry.created_at, "payload": entry.payload} for key, entry in _CACHE.items()}
    try:
        tmp = _CACHE_FILE.with_suffix(_CACHE_FILE.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, _CACHE_FILE)
        return len(data)
    except OSError:
        return 0


def get_cache_stats() -> dict[str, Any]:
    with _LOCK:
        return {"size": len(_CACHE), "max_items": _DEFAULT_MAX_ITEMS, "ttl_seconds": _DEFAULT_TTL_SECONDS}
