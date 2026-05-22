from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Any

from ..repositories import normalize_search_text


@dataclass
class CacheEntry:
    created_at: float
    payload: dict[str, Any]


_LOCK = threading.Lock()
_CACHE: dict[str, CacheEntry] = {}

_DEFAULT_TTL_SECONDS = int(os.getenv("ANSWER_CACHE_TTL_SECONDS", "21600") or "21600")
_DEFAULT_MAX_ITEMS = int(os.getenv("ANSWER_CACHE_MAX_ITEMS", "200") or "200")


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
