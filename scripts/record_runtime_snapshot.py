#!/usr/bin/env python3
"""记录一次运行态快照，作为 7×24 / 3个月试运行证据骨架。"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_demo_password() -> str:
    configured = os.getenv("DEMO_PASSWORD", "").strip()
    if configured:
        return configured
    env_file = REPO_ROOT / ".env.web_demo"
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and key.strip() == "DEMO_PASSWORD":
            return value.strip().strip('"')
    return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record one runtime snapshot")
    parser.add_argument("--base-url", default="http://127.0.0.1:8091", help="Demo base URL")
    parser.add_argument(
        "--runtime-file",
        default=str(REPO_ROOT / "artifacts" / "local-dify-rag" / "runtime.json"),
        help="Path to local runtime.json",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "artifacts" / "runtime"),
        help="Directory for runtime snapshots",
    )
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout seconds")
    parser.add_argument("--demo-password", default=load_demo_password(), help=argparse.SUPPRESS)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fetch_json(
    url: str,
    timeout: int,
    demo_password: str = "",
) -> tuple[int, dict[str, Any], str]:
    resp = None
    try:
        resp = requests.get(
            url,
            headers={"x-password": demo_password} if demo_password else {},
            timeout=(8, timeout),
        )
        payload: dict[str, Any] = {}
        err = ""
        try:
            payload = resp.json()
        except Exception:
            err = resp.text[:300]
        return resp.status_code, payload, err
    except Exception as exc:
        return 0, {}, str(exc)
    finally:
        if resp is not None:
            resp.close()


def append_csv(path: Path, row: dict[str, Any], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    runtime_file = Path(args.runtime_file).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    runtime = load_json(runtime_file)
    health_status, health_payload, health_error = fetch_json(
        f"{base_url}/health", args.timeout, args.demo_password
    )
    meta_status, meta_payload, meta_error = fetch_json(
        f"{base_url}/api/meta", args.timeout, args.demo_password
    )
    stats_status, stats_payload, stats_error = fetch_json(
        f"{base_url}/api/stats", args.timeout, args.demo_password
    )

    dify_base_url = str(health_payload.get("dify_base_url") or meta_payload.get("dify_base_url") or "")
    dify_host = ""
    if dify_base_url:
        parsed = urlparse(dify_base_url)
        dify_host = f"{parsed.scheme}://{parsed.netloc}"

    snapshot = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "base_url": base_url,
        "health_status": health_status,
        "health_ok": bool(health_payload.get("ok", False)),
        "health_error": health_error,
        "kb_loaded": health_payload.get("kb_loaded", ""),
        "dify_reachable": health_payload.get("dify_reachable", ""),
        "dify_error": health_payload.get("dify_error", "") or meta_error or stats_error,
        "meta_status": meta_status,
        "knowledge_base_rows": meta_payload.get("knowledge_base_rows", ""),
        "knowledge_base_imported": meta_payload.get("knowledge_base_imported", ""),
        "knowledge_base_chunked": meta_payload.get("knowledge_base_chunked", ""),
        "knowledge_base_external": meta_payload.get("knowledge_base_external", ""),
        "stats_status": stats_status,
        "recent_count": stats_payload.get("recent_count", ""),
        "recent_avg_ms": stats_payload.get("recent_avg_ms", ""),
        "recent_p50_ms": stats_payload.get("recent_p50_ms", ""),
        "recent_p95_ms": stats_payload.get("recent_p95_ms", ""),
        "recent_max_ms": stats_payload.get("recent_max_ms", ""),
        "recent_cache_hit_rate": stats_payload.get("recent_cache_hit_rate", ""),
        "runtime_started_at": runtime.get("started_at", ""),
        "runtime_pid": runtime.get("pid", ""),
        "runtime_url": runtime.get("url", ""),
        "runtime_python": runtime.get("python_exe", ""),
        "dify_host": dify_host,
    }

    jsonl_path = out_dir / "health_snapshots.jsonl"
    with jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

    csv_headers = list(snapshot.keys())
    csv_path = out_dir / "health_snapshots.csv"
    append_csv(csv_path, snapshot, csv_headers)

    print(f"[OK] snapshot jsonl appended: {jsonl_path}")
    print(f"[OK] snapshot csv appended: {csv_path}")
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
