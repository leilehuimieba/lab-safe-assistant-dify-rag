#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from libs.kb_schema import KB_HEADERS

REQUIRED_KB_HEADERS = list(KB_HEADERS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal quality gate for the extracted Dify RAG project.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--skip-secret-scan", action="store_true", help="Kept for compatibility with the old command line.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).resolve()
    errors: list[str] = []

    required_files = [
        "web_demo/app.py",
        "web_demo/routers/chat_routes.py",
        "web_demo/services/upstream_service.py",
        "web_demo/services/kb_service.py",
        "web_demo/services/session_service.py",
        "web_demo/templates/index.html",
        "knowledge_base_curated.csv",
        "safety_rules.yaml",
        ".env.dify_rag.example",
        "scripts/start_dify_rag_local.ps1",
        "scripts/run_eval_batch.py",
        "scripts/perf_benchmark.py",
        "scripts/kb_watcher.py",
    ]
    for rel in required_files:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")

    kb_path = root / "knowledge_base_curated.csv"
    if kb_path.exists():
        raw = kb_path.read_bytes()
        nul_count = raw.count(b"\x00")
        if nul_count > 0:
            errors.append(f"knowledge_base_curated.csv contains {nul_count} NUL bytes")

        with kb_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            headers = list(reader.fieldnames or [])
            rows = list(reader)
        missing_headers = [h for h in REQUIRED_KB_HEADERS if h not in headers]
        if missing_headers:
            errors.append(f"knowledge_base_curated.csv missing headers: {missing_headers}")
        if len(rows) < 1000:
            errors.append(f"knowledge_base_curated.csv row count too small: {len(rows)} < 1000")
        duplicate_ids = sorted({r.get("id", "") for r in rows if r.get("id", "") and sum(1 for x in rows if x.get("id", "") == r.get("id", "")) > 1})
        if duplicate_ids:
            errors.append(f"knowledge_base_curated.csv duplicate ids: {duplicate_ids[:10]}")
        for idx, row in enumerate(rows[:200], start=2):
            if not (row.get("id") or "").strip():
                errors.append(f"knowledge_base_curated.csv line {idx}: empty id")
            if not (row.get("question") or "").strip() and not (row.get("answer") or "").strip():
                errors.append(f"knowledge_base_curated.csv line {idx}: both question and answer are empty")
        # risk_level range check (sample first 500 rows)
        for idx, row in enumerate(rows[:500], start=2):
            risk = (row.get("risk_level") or "").strip()
            if risk:
                try:
                    v = int(float(risk))
                    if v < 1 or v > 5:
                        errors.append(f"knowledge_base_curated.csv line {idx}: risk_level out of range: {risk}")
                except ValueError:
                    errors.append(f"knowledge_base_curated.csv line {idx}: risk_level not numeric: {risk}")
        # source_url format check (spot-check first 100 non-empty urls)
        urls_checked = 0
        for row in rows:
            url = (row.get("source_url") or "").strip()
            if url and urls_checked < 100:
                urls_checked += 1
                if not (url.startswith("http://") or url.startswith("https://")):
                    errors.append(f"knowledge_base_curated.csv: invalid source_url format: {url[:80]}")

    # Import smoke test.
    try:
        import os
        import sys as _sys
        _sys.path.insert(0, str(root))
        from web_demo.app import app  # noqa: F401
        from web_demo.services import retrieve_citations, get_or_create
        from web_demo.models import ChatRequest, ChatResponse, FeedbackRequest, StatsResponse
        hits = retrieve_citations("化学品泄漏怎么办", top_k=3)
        if not hits:
            errors.append("retrieve_citations returned no hits for smoke query")
        sess = get_or_create()
        if not sess.session_id:
            errors.append("session_service: get_or_create returned empty session_id")
    except Exception as exc:
        errors.append(f"import/retrieval smoke failed: {exc}")

    if errors:
        print("Quality gate failed with issues:")
        for item in errors:
            print(f"- {item}")
        return 1
    print("Quality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

