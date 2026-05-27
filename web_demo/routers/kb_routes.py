from __future__ import annotations

from fastapi import APIRouter, Depends

from ..repositories import load_kb_entries
from ..services.auth_service import verify_password
from ..services.kb_usage_service import get_called_kb_ids, get_call_counts

router = APIRouter(dependencies=[Depends(verify_password)])


@router.get("/api/kb/summary")
def kb_summary() -> dict:
    kb = load_kb_entries()
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

    return {
        "total_entries": total,
        "total_categories": len(categories),
        "called_entries": called_total,
        "coverage_rate": round((called_total / total) * 100, 1) if total > 0 else 0.0,
        "categories": categories,
    }


@router.get("/api/kb/entries")
def kb_entries(category: str = "", subcategory: str = "", offset: int = 0, limit: int = 50) -> dict:
    kb = load_kb_entries()
    called_ids = get_called_kb_ids()
    call_counts = get_call_counts()

    filtered = []
    cat_filter = category.strip()
    sub_filter = subcategory.strip()

    for row in kb:
        row_cat = (row.get("category") or "").strip()
        row_sub = (row.get("subcategory") or "").strip()
        if cat_filter and row_cat != cat_filter:
            continue
        if sub_filter and row_sub != sub_filter:
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
            "source_org": row.get("source_org", ""),
            "source_url": row.get("source_url", ""),
            "question": row.get("question", ""),
            "answer": row.get("answer", "")[:300],
        })

    total = len(filtered)
    offset = max(0, offset)
    limit = max(1, min(200, limit))
    page = filtered[offset:offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "entries": page,
    }
