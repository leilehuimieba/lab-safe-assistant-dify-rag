from __future__ import annotations

import csv
import os
import re
import threading
from pathlib import Path
from typing import Any

from libs.common_io import write_csv_row
from libs.text_utils import normalize_search_text, extract_tokens

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
HTML_FILE = BASE_DIR / "templates" / "index.html"
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
RULES_FILE = REPO_ROOT / "safety_rules.yaml"
LOW_CONFIDENCE_QUEUE_FILE = REPO_ROOT / "artifacts" / "low_confidence_followups" / "data_gap_queue.csv"

APP_VERSION = "dify-rag-project-1"
FORMAL_EVAL_SCORE = "50题HTTP 50/50；内容待专家复核"
STABILITY_EVIDENCE = "7×24监测累积中（2026-07-01起）"
KB_IMPORT_SUCCESS_COUNT = int(os.getenv("KB_IMPORT_SUCCESS_COUNT", "398") or "398")
KB_CHUNK_IMPORT_COUNT = int(os.getenv("KB_CHUNK_IMPORT_COUNT", "3164") or "3164")
KB_EXTERNAL_IMPORT_COUNT = int(os.getenv("KB_EXTERNAL_IMPORT_COUNT", "1159") or "1159")

DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "4") or "4")
DEFAULT_LOW_CONFIDENCE_TOP_SCORE = float(os.getenv("LOW_CONFIDENCE_TOP_SCORE", "3.5") or "3.5")
DIFY_DEFAULT_BASE_URL = "http://127.0.0.1:8081"
DIFY_DEFAULT_TIMEOUT = 120.0

# 仅保留兜底兼容常量；本项目主链路是 Dify + RAG。
DEFAULT_BASE_URL = "http://127.0.0.1:3000/v1"
DEFAULT_MODEL = "openai-compatible-model"
DEFAULT_FALLBACK_MODELS = ""
SYSTEM_PROMPTS = {
    "lab": (
        "You are a laboratory safety assistant. Output in this order: conclusion, steps, "
        "forbidden actions, escalation. Never provide unsafe instructions. "
        "If the question is outside laboratory safety scope (chemicals, equipment, emergency, "
        "PPE, regulations, lab SOPs), politely decline in one or two sentences and explain "
        "your scope instead of producing a fabricated safety answer. Never invent safety "
        "advice for unrelated topics such as weather, cooking, entertainment, coding, or "
        "general chitchat."
    ),
    "agent": "You are a concise project copilot.",
}

SEVERITY_SCORE = {"critical": 5, "high": 4, "medium": 3, "low": 2}
TERMINAL_ACTIONS = {"refuse", "redirect_emergency", "ask_for_more_info", "direct_safe_answer"}
REFUSE_INTENT_MARKERS = [
    "能不能", "可不可以", "可以吗", "绕过", "规避", "跳过", "怎么混", "混吗", "一起混",
    "直接倒", "倒掉", "下水道", "明火", "酒精灯", "加热", "不开通风柜", "不用通风", "不戴",
    "省略ppe", "直接开", "运转时开盖",
]
EMERGENCY_INTENT_MARKERS = [
    "怎么办", "怎么处理", "如何处理", "第一步", "应急", "事故", "紧急", "受伤", "泄漏", "起火", "着火", "冒烟", "暴露",
]
RISK_LABEL = {1: "Low", 2: "Medium-Low", 3: "Medium", 4: "High", 5: "Critical"}

QUEUE_HEADERS = [
    "created_at", "question_hash", "question", "mode", "decision", "risk_level", "matched_rule_id",
    "matched_rule_action", "low_confidence_reason", "citation_count", "top_score", "top_kb_id",
    "top_source_title", "suggested_lane", "suggested_action", "status", "notes",
]

_CACHE_LOCK = threading.Lock()
_QUEUE_LOCK = threading.Lock()
_KB_CACHE: list[dict[str, str]] | None = None
_RULES_CACHE: dict[str, Any] | None = None


def safe_read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.DictReader(f)]


def load_kb_entries() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not KB_FILE.exists():
        return rows
    with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            title = (row.get("title") or "").strip()
            question = (row.get("question") or "").strip()
            answer = (row.get("answer") or "").strip()
            steps = (row.get("steps") or "").strip()
            forbidden = (row.get("forbidden") or "").strip()
            emergency = (row.get("emergency") or "").strip()
            first_aid = (row.get("first_aid") or "").strip()
            ppe = (row.get("ppe") or "").strip()
            hazard_types = (row.get("hazard_types") or "").strip()
            tags = (row.get("tags") or "").strip()
            blob = normalize_search_text(" ".join([title, question, answer, steps, forbidden, emergency, first_aid, ppe, hazard_types, tags]))
            title_blob = normalize_search_text(" ".join([title, question]))
            tag_blob = normalize_search_text(" ".join([hazard_types, tags]))
            body_blob = normalize_search_text(" ".join([answer, steps, forbidden, emergency, first_aid, ppe]))
            rows.append({
                "id": (row.get("id") or "").strip(),
                "title": title,
                "question": question,
                "source_title": (row.get("source_title") or "").strip(),
                "source_org": (row.get("source_org") or "").strip(),
                "source_url": (row.get("source_url") or "").strip(),
                "risk_level": (row.get("risk_level") or "").strip(),
                "category": (row.get("category") or "").strip(),
                "subcategory": (row.get("subcategory") or "").strip(),
                "hazard_types": hazard_types,
                "answer": answer,
                "steps": steps,
                "forbidden": forbidden,
                "emergency": emergency,
                "first_aid": first_aid,
                "ppe": ppe,
                "tags": tags,
                "title_blob": title_blob,
                "tag_blob": tag_blob,
                "body_blob": body_blob,
                "blob": blob,
                # Pre-computed token sets for fast lookup
                "title_tokens": extract_tokens(title_blob),
                "tag_tokens": extract_tokens(tag_blob),
                "body_tokens": extract_tokens(body_blob),
                "all_tokens": extract_tokens(blob),
            })
    return rows


def get_kb_entries() -> list[dict[str, str]]:
    global _KB_CACHE
    with _CACHE_LOCK:
        if _KB_CACHE is None:
            _KB_CACHE = load_kb_entries()
        return _KB_CACHE


def load_rules_config() -> dict[str, Any]:
    if yaml is None or not RULES_FILE.exists():
        return {"rules": []}
    with RULES_FILE.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    return payload if isinstance(payload, dict) else {"rules": []}


def get_rules_config() -> dict[str, Any]:
    global _RULES_CACHE
    with _CACHE_LOCK:
        if _RULES_CACHE is None:
            _RULES_CACHE = load_rules_config()
        return _RULES_CACHE
