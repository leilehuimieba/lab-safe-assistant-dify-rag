from __future__ import annotations

import os
import time
from collections import OrderedDict
from threading import RLock

from fastapi import APIRouter, Depends

from libs.text_utils import normalize_search_text

from ..repositories import get_kb_entries
from ..services.auth_service import verify_password
from ..services.kb_usage_service import get_called_kb_ids, get_call_counts

router = APIRouter(dependencies=[Depends(verify_password)])

_ENTRIES_CACHE_MAX = 48
_ENTRIES_CACHE_LOCK = RLock()
_ENTRIES_CACHE: OrderedDict[tuple[str, str, str, str, str], tuple[float, list[dict]]] = OrderedDict()
_SUMMARY_CACHE_LOCK = RLock()
_SUMMARY_CACHE: dict[str, tuple[float, dict]] = {}


def _entries_cache_ttl_seconds() -> int:
    try:
        return max(0, int(os.getenv("KB_ENTRIES_CACHE_SECONDS", "10") or "10"))
    except ValueError:
        return 10


def _summary_cache_ttl_seconds() -> int:
    try:
        return max(0, int(os.getenv("KB_SUMMARY_CACHE_SECONDS", "10") or "10"))
    except ValueError:
        return 10


def _get_cached_summary() -> dict | None:
    ttl = _summary_cache_ttl_seconds()
    if ttl <= 0:
        return None
    now = time.monotonic()
    with _SUMMARY_CACHE_LOCK:
        cached = _SUMMARY_CACHE.get("summary")
        if not cached:
            return None
        created_at, payload = cached
        if now - created_at > ttl:
            _SUMMARY_CACHE.pop("summary", None)
            return None
        return {**payload, "cache_hit": True}


def _set_cached_summary(payload: dict) -> None:
    ttl = _summary_cache_ttl_seconds()
    if ttl <= 0:
        return
    cached_payload = {**payload, "cache_hit": False}
    with _SUMMARY_CACHE_LOCK:
        _SUMMARY_CACHE["summary"] = (time.monotonic(), cached_payload)


def _get_cached_entries(key: tuple[str, str, str, str, str]) -> list[dict] | None:
    ttl = _entries_cache_ttl_seconds()
    if ttl <= 0:
        return None
    now = time.monotonic()
    with _ENTRIES_CACHE_LOCK:
        cached = _ENTRIES_CACHE.get(key)
        if not cached:
            return None
        created_at, entries = cached
        if now - created_at > ttl:
            _ENTRIES_CACHE.pop(key, None)
            return None
        _ENTRIES_CACHE.move_to_end(key)
        return entries


def _set_cached_entries(key: tuple[str, str, str, str, str], entries: list[dict]) -> None:
    ttl = _entries_cache_ttl_seconds()
    if ttl <= 0:
        return
    with _ENTRIES_CACHE_LOCK:
        _ENTRIES_CACHE[key] = (time.monotonic(), entries)
        _ENTRIES_CACHE.move_to_end(key)
        while len(_ENTRIES_CACHE) > _ENTRIES_CACHE_MAX:
            _ENTRIES_CACHE.popitem(last=False)


@router.get("/api/kb/summary")
def kb_summary() -> dict:
    cached = _get_cached_summary()
    if cached:
        return cached

    kb = get_kb_entries()
    called_ids = get_called_kb_ids()
    call_counts = get_call_counts()

    cat_map: dict[str, dict] = {}
    total = len(kb)
    called_total = 0

    for row in kb:
        cat = (row.get("category") or "").strip() or "未分类"
        sub = (row.get("subcategory") or "").strip() or "未分类"
        kb_id = row.get("id", "").strip()
        is_called = kb_id in called_ids
        count = call_counts.get(kb_id, 0)

        if cat not in cat_map:
            cat_map[cat] = {
                "name": cat,
                "count": 0,
                "called_count": 0,
                "subcategories": {},
            }
        cat_map[cat]["count"] += 1
        if is_called:
            cat_map[cat]["called_count"] += 1
            called_total += 1

        sub_map = cat_map[cat]["subcategories"]
        if sub not in sub_map:
            sub_map[sub] = {"name": sub, "count": 0, "called_count": 0}
        sub_map[sub]["count"] += 1
        if is_called:
            sub_map[sub]["called_count"] += 1

    categories = []
    for cat_data in cat_map.values():
        cat_count = cat_data["count"]
        cat_called = cat_data["called_count"]
        sub_list = []
        for sub_data in cat_data["subcategories"].values():
            sub_count = sub_data["count"]
            sub_called = sub_data["called_count"]
            sub_list.append({
                "name": sub_data["name"],
                "count": sub_count,
                "called_count": sub_called,
                "coverage_rate": round((sub_called / sub_count) * 100, 1) if sub_count > 0 else 0.0,
            })
        sub_list.sort(key=lambda x: x["count"], reverse=True)
        categories.append({
            "name": cat_data["name"],
            "count": cat_count,
            "called_count": cat_called,
            "coverage_rate": round((cat_called / cat_count) * 100, 1) if cat_count > 0 else 0.0,
            "subcategories": sub_list,
        })

    categories.sort(key=lambda x: x["count"], reverse=True)

    payload = {
        "total_entries": total,
        "total_categories": len(categories),
        "called_entries": called_total,
        "coverage_rate": round((called_total / total) * 100, 1) if total > 0 else 0.0,
        "categories": categories,
        "cache_hit": False,
    }
    _set_cached_summary(payload)
    return payload


@router.get("/api/kb/entries")
def kb_entries(
    category: str = "",
    subcategory: str = "",
    keyword: str = "",
    offset: int = 0,
    limit: int = 120,
    sort_by: str = "call_count",
    sort_order: str = "desc",
) -> dict:
    cat_filter = category.strip()
    sub_filter = subcategory.strip()
    keyword_filter = normalize_search_text(keyword)
    sort_key = (sort_by or "call_count").strip().lower()
    reverse = (sort_order or "desc").strip().lower() != "asc"
    normalized_sort_order = "desc" if reverse else "asc"

    cache_key = (cat_filter, sub_filter, keyword_filter, sort_key, normalized_sort_order)
    filtered = _get_cached_entries(cache_key)
    cache_hit = filtered is not None

    def _risk_rank(value: str) -> tuple[int, str]:
        text = (value or "").strip()
        if text.isdigit():
            return int(text), text
        mapping = {"low": 1, "medium-low": 2, "medium": 3, "high": 4, "critical": 5}
        return mapping.get(text.lower(), 0), text

    def _sorter(item: dict) -> tuple:
        title = (item.get("title") or item.get("id") or "").strip().lower()
        if sort_key == "title":
            return title, item.get("id", "")
        if sort_key == "risk_level":
            risk_rank, risk_text = _risk_rank(str(item.get("risk_level", "")))
            return risk_rank, risk_text, title
        if sort_key == "called":
            return int(bool(item.get("called"))), int(item.get("call_count") or 0), title
        return int(item.get("call_count") or 0), int(bool(item.get("called"))), title

    if filtered is None:
        kb = get_kb_entries()
        called_ids = set(get_called_kb_ids())
        call_counts = get_call_counts()

        filtered = []
        for row in kb:
            row_cat = (row.get("category") or "").strip() or "未分类"
            row_sub = (row.get("subcategory") or "").strip() or "未分类"
            if cat_filter and row_cat != cat_filter:
                continue
            if sub_filter and row_sub != sub_filter:
                continue
            if keyword_filter and keyword_filter not in row.get("blob", ""):
                continue
            kb_id = row.get("id", "").strip()
            filtered.append({
                "id": kb_id,
                "title": row.get("title", ""),
                "category": row_cat or "未分类",
                "subcategory": row_sub or "未分类",
                "risk_level": row.get("risk_level", ""),
                "called": kb_id in called_ids,
                "call_count": call_counts.get(kb_id, 0),
                "source_title": row.get("source_title", ""),
                "source_org": row.get("source_org", ""),
                "source_url": row.get("source_url", ""),
                "question": row.get("question", ""),
                "answer": row.get("answer", "")[:300],
            })

        filtered.sort(key=_sorter, reverse=reverse)
        _set_cached_entries(cache_key, filtered)

    total = len(filtered)
    offset = max(0, offset)
    limit = max(20, min(240, limit))
    page = filtered[offset:offset + limit]
    next_offset = offset + len(page)

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": next_offset < total,
        "next_offset": next_offset if next_offset < total else None,
        "sort_by": sort_key,
        "sort_order": normalized_sort_order,
        "keyword": keyword.strip(),
        "cache_hit": cache_hit,
        "entries": page,
    }
