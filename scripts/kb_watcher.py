#!/usr/bin/env python3
"""知识库动态更新监控 —— 轮询 data_sources/incoming/ 目录，自动合并新增条目。

用法（前台运行，每 30 秒检查一次）：
    python scripts/kb_watcher.py --interval 30

用法（单次检查并合并）：
    python scripts/kb_watcher.py --once
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = REPO_ROOT / "data_sources" / "incoming"
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
CHANGELOG_DIR = REPO_ROOT / "artifacts" / "kb_changelog"
PROCESSED_DIR = INCOMING_DIR / ".processed"

KB_REQUIRED_COLS = ["id", "title", "category", "question", "answer"]
KB_ALL_COLS: list[str] = []


def _detect_kb_columns() -> list[str]:
    global KB_ALL_COLS
    if KB_ALL_COLS:
        return KB_ALL_COLS
    if KB_FILE.exists():
        with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            KB_ALL_COLS = list(reader.fieldnames or [])
    return KB_ALL_COLS


def read_csv_safe(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    raw = path.read_bytes()
    raw = raw.replace(b"\x00", b"")
    lines = raw.decode("utf-8-sig").splitlines()
    if not lines:
        return []
    reader = csv.DictReader(lines)
    return [row for row in reader]


def validate_row(row: dict[str, str], idx: int) -> list[str]:
    errors: list[str] = []
    rid = row.get("id", f"row_{idx}")
    for col in KB_REQUIRED_COLS:
        if not (row.get(col) or "").strip():
            errors.append(f"[{rid}] missing required field: {col}")
    risk = (row.get("risk_level") or "").strip()
    if risk:
        try:
            v = int(float(risk))
            if v < 1 or v > 5:
                errors.append(f"[{rid}] risk_level out of range: {risk}")
        except ValueError:
            errors.append(f"[{rid}] risk_level not numeric: {risk}")
    return errors


def merge_into_kb(new_rows: list[dict[str, str]]) -> dict[str, Any]:
    """将新条目合并到主知识库，按 id 去重。返回变更摘要。"""
    existing = read_csv_safe(KB_FILE)
    existing_ids: set[str] = {r.get("id", "").strip() for r in existing if r.get("id", "").strip()}
    all_cols = _detect_kb_columns()

    added: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []

    new_by_id: dict[str, dict[str, str]] = {}
    for row in new_rows:
        rid = (row.get("id") or "").strip()
        if not rid:
            skipped.append("(empty_id)")
            continue
        if rid in new_by_id:
            skipped.append(f"{rid}(duplicate_in_batch)")
            continue
        new_by_id[rid] = row

    for rid, row in new_by_id.items():
        if rid in existing_ids:
            idx = next((i for i, r in enumerate(existing) if r.get("id", "").strip() == rid), None)
            if idx is not None:
                existing[idx] = row
                updated.append(rid)
            else:
                existing.append(row)
                added.append(rid)
        else:
            normalized = {k: row.get(k, "") for k in all_cols}
            existing.append(normalized)
            added.append(rid)
            existing_ids.add(rid)

    # Write back
    if added or updated:
        with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_cols, extrasaction="ignore")
            writer.writeheader()
            for row in existing:
                writer.writerow(row)

    return {"added": added, "updated": updated, "skipped": skipped, "total": len(existing)}


def write_changelog(summary: dict[str, Any], source_file: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = CHANGELOG_DIR / f"changelog_{ts}.json"
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source_file": source_file,
        **summary,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def process_incoming() -> dict[str, Any]:
    """处理 incoming 目录中所有新 CSV 文件。"""
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(INCOMING_DIR.glob("*.csv"))
    if not csv_files:
        return {"status": "no_files"}

    total_added = 0
    total_updated = 0
    total_errors = 0

    for csv_path in csv_files:
        print(f"Processing: {csv_path.name}")
        rows = read_csv_safe(csv_path)
        if not rows:
            print(f"  empty file, skipping")
            csv_path.rename(PROCESSED_DIR / csv_path.name)
            continue

        errors = []
        for idx, row in enumerate(rows, 1):
            errs = validate_row(row, idx)
            if errs:
                errors.extend(errs)

        if errors:
            print(f"  validation errors ({len(errors)}):")
            for e in errors[:10]:
                print(f"    {e}")
            total_errors += len(errors)
            if len(errors) == len(rows):
                print(f"  all rows failed, skipping file")
                csv_path.rename(PROCESSED_DIR / f"{csv_path.name}.failed")
                continue

        summary = merge_into_kb(rows)
        changelog_path = write_changelog(summary, csv_path.name)
        print(f"  added={len(summary['added'])} updated={len(summary['updated'])} skipped={len(summary['skipped'])} total={summary['total']}")
        print(f"  changelog: {changelog_path.name}")

        total_added += len(summary["added"])
        total_updated += len(summary["updated"])

        # Move processed file
        dest = PROCESSED_DIR / csv_path.name
        if dest.exists():
            dest = PROCESSED_DIR / f"{csv_path.stem}_{int(time.time())}.csv"
        csv_path.rename(dest)

    return {
        "status": "ok",
        "files_processed": len(csv_files),
        "added": total_added,
        "updated": total_updated,
        "errors": total_errors,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KB file watcher for incremental updates")
    p.add_argument("--interval", type=int, default=30, help="Polling interval in seconds (default: 30)")
    p.add_argument("--once", action="store_true", help="Run once and exit")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.once:
        result = process_incoming()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"Watching {INCOMING_DIR} every {args.interval}s...")
    print(f"Drop .csv files into the directory to auto-merge into {KB_FILE.name}")
    print(f"Press Ctrl+C to stop.\n")

    try:
        while True:
            result = process_incoming()
            if result.get("status") != "no_files":
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {result}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nWatcher stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
