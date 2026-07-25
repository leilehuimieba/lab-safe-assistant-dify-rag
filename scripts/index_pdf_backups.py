#!/usr/bin/env python3
"""Index local PDF source backups and rebuild auditable manifests.

The PDF downloader intentionally embeds ``sha1(source_url)[:10]`` in every saved
filename.  This script scans the backup directory, validates PDF magic, maps each
file back to the audited source URL, and writes:

- a file-level index for manual inspection;
- a success manifest consumable by ``audit_source_backup_coverage.py``;
- a compact JSON summary with final PDF coverage counts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COVERAGE = (
    REPO_ROOT / "artifacts/source_backup_coverage_20260725/source_backup_coverage.csv"
)
DEFAULT_BACKUP_DIR = REPO_ROOT / "artifacts/pdf_source_backups_20260725"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def looks_like_pdf(path: Path) -> bool:
    prefix = path.read_bytes()[:2048].lstrip(b"\xef\xbb\xbf\r\n\t ")
    return prefix.startswith(b"%PDF-")


def source_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    args = parser.parse_args()

    files_dir = args.backup_dir / "files"
    coverage_rows = read_csv(args.coverage)
    by_hash = {
        source_hash(row["url"]): row
        for row in coverage_rows
        if (row.get("url") or "").strip()
    }
    replacement_rows = {
        row.get("source_url", ""): row
        for row in read_csv(args.backup_dir / "pdf_url_replacements_20260725.csv")
        if row.get("source_url")
    }

    now = datetime.now(timezone.utc).isoformat()
    index_rows: list[dict[str, str]] = []
    manifest_by_url: dict[str, dict[str, str]] = {}

    for path in sorted(files_dir.glob("*.pdf")):
        parts = path.name.split("_")
        matched_hash = next((part for part in parts if part in by_hash), "")
        if not matched_hash:
            continue
        source = by_hash[matched_hash]
        source_url = source["url"]
        if not looks_like_pdf(path):
            continue
        data = path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        size = str(len(data))
        replacement = replacement_rows.get(source_url, {})
        row = {
            "source_url": source_url,
            "row_count": source.get("row_count", ""),
            "traceability_status": source.get("traceability_status", ""),
            "content_type": source.get("content_type", ""),
            "url_hash": matched_hash,
            "local_path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256,
            "size_bytes": size,
            "replacement_url": replacement.get("replacement_url", ""),
            "indexed_at": now,
        }
        index_rows.append(row)

        # Keep one deterministic manifest row per source URL.  If a replacement
        # row exists, preserve the canonical replacement URL as final_url.
        manifest_by_url.setdefault(source_url, {
            "source_url": source_url,
            "row_count": source.get("row_count", ""),
            "traceability_status": source.get("traceability_status", ""),
            "attempted_url": replacement.get("replacement_url", source_url),
            "final_url": replacement.get("replacement_url", source_url),
            "http_status": "",
            "content_type": "application/pdf",
            "status": "downloaded",
            "local_path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256,
            "size_bytes": size,
            "retrieved_at": now,
            "notes": replacement.get("reason", "validated_pdf_magic_from_local_backup_index"),
        })

    index_path = args.backup_dir / "pdf_backup_file_index_20260725.csv"
    manifest_path = args.backup_dir / "pdf_backup_manifest_20260725.csv"
    failed_path = args.backup_dir / "pdf_backup_failed_attempts_20260725.csv"
    write_csv(index_path, index_rows, [
        "source_url",
        "row_count",
        "traceability_status",
        "content_type",
        "url_hash",
        "local_path",
        "sha256",
        "size_bytes",
        "replacement_url",
        "indexed_at",
    ])
    manifest_rows = [manifest_by_url[url] for url in sorted(manifest_by_url)]
    write_csv(manifest_path, manifest_rows, [
        "source_url",
        "row_count",
        "traceability_status",
        "attempted_url",
        "final_url",
        "http_status",
        "content_type",
        "status",
        "local_path",
        "sha256",
        "size_bytes",
        "retrieved_at",
        "notes",
    ])

    pdf_source_urls = [
        row for row in coverage_rows
        if row.get("is_pdf_source") == "yes"
    ]
    missing_rows = [
        row for row in pdf_source_urls
        if row.get("has_local_pdf") != "yes" and row["url"] not in manifest_by_url
    ]
    write_csv(failed_path, [
        {
            "source_url": row["url"],
            "row_count": row.get("row_count", ""),
            "traceability_status": row.get("traceability_status", ""),
            "http_status": row.get("http_status", ""),
            "content_type": row.get("content_type", ""),
            "status": "missing_after_automated_attempts",
            "local_path": "",
            "retrieved_at": now,
            "notes": (
                "未保存为本地 PDF：自动化下载未取得可通过 %PDF- 校验的原件；"
                "需人工浏览器另存、换网络或替换为同机构现行下载端点。"
            ),
        }
        for row in missing_rows
    ], [
        "source_url",
        "row_count",
        "traceability_status",
        "http_status",
        "content_type",
        "status",
        "local_path",
        "retrieved_at",
        "notes",
    ])
    summary = {
        "generated_at": now,
        "pdf_files": len(index_rows),
        "unique_source_urls": len(manifest_by_url),
        "total_size_bytes": sum(int(row["size_bytes"]) for row in index_rows),
        "coverage_pdf_source_urls": len(pdf_source_urls),
        "coverage_pdf_with_local_pdf": sum(
            1 for row in pdf_source_urls
            if row.get("has_local_pdf") == "yes" or row["url"] in manifest_by_url
        ),
        "coverage_pdf_missing_local_pdf": sum(
            1 for row in pdf_source_urls
            if row.get("has_local_pdf") != "yes" and row["url"] not in manifest_by_url
        ),
        "manifest": str(manifest_path.relative_to(REPO_ROOT)),
        "file_index": str(index_path.relative_to(REPO_ROOT)),
        "failed_attempts": str(failed_path.relative_to(REPO_ROOT)),
    }
    (args.backup_dir / "pdf_backup_summary_20260725.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.backup_dir / "pdf_backup_file_index_summary_20260725.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
