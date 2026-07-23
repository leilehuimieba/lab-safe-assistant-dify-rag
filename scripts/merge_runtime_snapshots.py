#!/usr/bin/env python3
"""合并远程 7x24 运行快照到本地 git 仓库，按 (captured_at, base_url) 去重。

用于把远程服务器（如腾讯云主监测环境）上 record_runtime_snapshot.py 产生的
health_snapshots.jsonl，与本地 artifacts/runtime/health_snapshots.jsonl 合并，
不覆盖、不删除任何已有记录，只新增本地缺失的行，并按 captured_at 排序后
重写 .jsonl 与 .csv（保持字段顺序一致）。
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

FIELDNAMES = [
    "captured_at",
    "base_url",
    "health_status",
    "health_ok",
    "health_error",
    "kb_loaded",
    "dify_reachable",
    "dify_error",
    "meta_status",
    "knowledge_base_rows",
    "knowledge_base_imported",
    "knowledge_base_chunked",
    "knowledge_base_external",
    "stats_status",
    "recent_count",
    "recent_avg_ms",
    "recent_p50_ms",
    "recent_p95_ms",
    "recent_max_ms",
    "recent_cache_hit_rate",
    "runtime_started_at",
    "runtime_pid",
    "runtime_url",
    "runtime_python",
    "dify_host",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def dedup_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("captured_at", "")), str(row.get("base_url", "")))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge remote runtime snapshots into local files")
    parser.add_argument("--remote-jsonl", required=True, help="Path to a staged copy of the remote health_snapshots.jsonl")
    parser.add_argument(
        "--local-jsonl",
        default=str(REPO_ROOT / "artifacts" / "runtime" / "health_snapshots.jsonl"),
    )
    parser.add_argument(
        "--local-csv",
        default=str(REPO_ROOT / "artifacts" / "runtime" / "health_snapshots.csv"),
    )
    args = parser.parse_args()

    remote_path = Path(args.remote_jsonl)
    local_jsonl_path = Path(args.local_jsonl)
    local_csv_path = Path(args.local_csv)

    local_rows = load_jsonl(local_jsonl_path)
    remote_rows = load_jsonl(remote_path)

    seen = {dedup_key(r) for r in local_rows}
    new_rows = [r for r in remote_rows if dedup_key(r) not in seen]

    if not new_rows:
        print("[INFO] no new remote rows to merge (all already present locally)")
        return

    merged = local_rows + new_rows
    merged.sort(key=lambda r: str(r.get("captured_at", "")))

    with local_jsonl_path.open("w", encoding="utf-8", newline="\n") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with local_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in merged:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})

    print(f"[OK] merged {len(new_rows)} new row(s) from remote; total now {len(merged)} row(s)")
    for row in new_rows:
        print(f"  + {row.get('captured_at')} {row.get('base_url')}")


if __name__ == "__main__":
    main()
