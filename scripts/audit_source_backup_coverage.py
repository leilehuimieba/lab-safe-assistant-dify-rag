#!/usr/bin/env python3
"""Summarize live source reachability and local evidence/PDF backup coverage.

This script intentionally does not download or mutate source material. It joins the
latest URL audit with the existing public-ingest cache and source archive manifest,
so the result can be reproduced without claiming that a blocked URL is dead.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_local_path(value: str) -> Path | None:
    value = (value or "").strip()
    if not value or value.upper().startswith("N/A"):
        return None
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def build_backup_index(
    public_items: Iterable[dict[str, object]],
    raw_dir: Path,
    archive_rows: Iterable[dict[str, str]],
    pdf_backup_rows: Iterable[dict[str, str]] = (),
) -> dict[str, dict[str, object]]:
    """Build per-original-URL evidence records.

    Public ingest files are exact downloads of the listed URL. Archive-manifest
    files may be an official mirror, which is deliberately labelled ``mirror``.
    """
    index: dict[str, dict[str, object]] = {}

    for item in public_items:
        source_id = str(item.get("id") or "").strip()
        url = str(item.get("url") or "").strip()
        if not source_id or not url:
            continue
        paths = sorted(path for path in raw_dir.glob(f"{source_id}_*") if path.is_file())
        if not paths:
            continue
        index[url] = {
            "backup_kind": "original",
            "has_local_pdf": any(path.suffix.lower() == ".pdf" for path in paths),
            "paths": [str(path) for path in paths],
        }

    for row in archive_rows:
        original_url = (row.get("original_citation_url") or "").strip()
        mirror_url = (row.get("mirror_url") or "").strip()
        paths = []
        for field in ("local_original_path", "local_markdown_path"):
            path = resolve_local_path(row.get(field) or "")
            if path and path.is_file():
                paths.append(path)
        if not original_url or not paths:
            continue

        kind = "original" if not mirror_url or mirror_url == original_url else "mirror"
        existing = index.get(original_url)
        if existing and existing["backup_kind"] == "original":
            existing_paths = list(existing["paths"])
            existing_paths.extend(str(path) for path in paths if str(path) not in existing_paths)
            existing["paths"] = existing_paths
            existing["has_local_pdf"] = bool(existing["has_local_pdf"]) or any(
                path.suffix.lower() == ".pdf" for path in paths
            )
            continue

        index[original_url] = {
            "backup_kind": kind,
            "has_local_pdf": kind == "original"
            and any(path.suffix.lower() == ".pdf" for path in paths),
            "paths": [str(path) for path in paths],
        }

    for row in pdf_backup_rows:
        if (row.get("status") or "").strip() != "downloaded":
            continue
        original_url = (row.get("source_url") or "").strip()
        path = resolve_local_path(row.get("local_path") or "")
        if not original_url or not path or not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        manifest_kind = (row.get("backup_kind") or "original").strip() or "original"
        existing = index.get(original_url)
        if existing:
            existing_paths = list(existing["paths"])
            if str(path) not in existing_paths:
                existing_paths.append(str(path))
            existing["paths"] = existing_paths
            if existing.get("backup_kind") != "original":
                existing["backup_kind"] = manifest_kind
            existing["has_local_pdf"] = True
        else:
            index[original_url] = {
                "backup_kind": manifest_kind,
                "has_local_pdf": True,
                "paths": [str(path)],
            }

    return index


def is_pdf_source(row: dict[str, str]) -> bool:
    url = (row.get("url") or "").lower().split("?", 1)[0]
    content_type = (row.get("content_type") or "").lower()
    return url.endswith(".pdf") or "application/pdf" in content_type


def add_pdf_backup_files_by_url_hash(
    backup_index: dict[str, dict[str, object]],
    live_rows: Iterable[dict[str, str]],
    pdf_backup_dir: Path,
) -> None:
    """Index PDF files downloaded by ``download_missing_pdf_backups.py``.

    That downloader embeds the first 10 hex chars of SHA1(source_url) in the
    filename. Scanning the directory makes coverage robust even if a later retry
    manifest contains only failures.
    """
    if not pdf_backup_dir.is_dir():
        return
    files = [path for path in pdf_backup_dir.glob("*.pdf") if path.is_file()]
    if not files:
        return
    for row in live_rows:
        url = (row.get("url") or "").strip()
        if not url or not is_pdf_source(row):
            continue
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        matches = sorted(path for path in files if f"_{digest}_" in path.name)
        if not matches:
            continue
        existing = backup_index.get(url)
        if existing:
            existing_paths = list(existing["paths"])
            for path in matches:
                if str(path) not in existing_paths:
                    existing_paths.append(str(path))
            existing["paths"] = existing_paths
            # Legacy directory scans represent direct downloads.  If the
            # manifest already identified this file as an archive replay, keep
            # that more precise provenance instead of silently upgrading it.
            existing_kind = str(existing.get("backup_kind") or "")
            if "archive" not in existing_kind and "mirror" not in existing_kind:
                existing["backup_kind"] = "original"
            existing["has_local_pdf"] = True
        else:
            backup_index[url] = {
                "backup_kind": "original",
                "has_local_pdf": True,
                "paths": [str(path) for path in matches],
            }


def summarize_coverage(
    kb_rows: list[dict[str, str]],
    live_rows: list[dict[str, str]],
    backup_index: dict[str, dict[str, object]],
) -> dict[str, object]:
    source_urls = {(row.get("source_url") or "").strip() for row in kb_rows}
    source_urls.discard("")
    live_by_url = {(row.get("url") or "").strip(): row for row in live_rows}
    status_counts = Counter(
        (live_by_url.get(url, {}).get("traceability_status") or "not_audited")
        for url in source_urls
    )
    pdf_urls = {
        url for url in source_urls
        if url in live_by_url and is_pdf_source(live_by_url[url])
    }
    evidence_urls = source_urls.intersection(backup_index)
    original_urls = {
        url for url in evidence_urls
        if backup_index[url].get("backup_kind") == "original"
    }
    mirror_urls = evidence_urls - original_urls
    pdf_backup_urls = {
        url for url in pdf_urls
        if bool(backup_index.get(url, {}).get("has_local_pdf"))
    }

    # Every audited status must survive into the summary. Enumerating only a few
    # known keys silently dropped ``bad_http_status`` before, so the published
    # breakdown did not add up to ``unique_source_urls``.
    named_statuses = ("open", "blocked_or_forbidden", "network_error", "bad_http_status", "not_audited")
    other_status_urls = sum(
        count for status, count in status_counts.items() if status not in named_statuses
    )

    summary = {
        "kb_rows": len(kb_rows),
        "unique_source_urls": len(source_urls),
        "open_urls": status_counts["open"],
        "blocked_or_forbidden_urls": status_counts["blocked_or_forbidden"],
        "network_error_urls": status_counts["network_error"],
        "bad_http_status_urls": status_counts["bad_http_status"],
        "not_audited_urls": status_counts["not_audited"],
        "other_status_urls": other_status_urls,
        "status_counts": dict(sorted(status_counts.items())),
        "urls_with_local_evidence": len(evidence_urls),
        "urls_with_original_download": len(original_urls),
        "urls_with_archive_mirror": len(mirror_urls),
        "rows_with_local_evidence": sum(
            1 for row in kb_rows
            if (row.get("source_url") or "").strip() in evidence_urls
        ),
        "pdf_source_urls": len(pdf_urls),
        "pdf_urls_with_local_pdf": len(pdf_backup_urls),
        "pdf_urls_missing_local_pdf": len(pdf_urls - pdf_backup_urls),
    }

    breakdown = sum(summary[key] for key in (
        "open_urls",
        "blocked_or_forbidden_urls",
        "network_error_urls",
        "bad_http_status_urls",
        "not_audited_urls",
        "other_status_urls",
    ))
    if breakdown != summary["unique_source_urls"]:
        raise ValueError(
            f"status breakdown {breakdown} != unique_source_urls {summary['unique_source_urls']}"
        )
    return summary


def write_outputs(
    kb_rows: list[dict[str, str]],
    live_rows: list[dict[str, str]],
    backup_index: dict[str, dict[str, object]],
    output_dir: Path,
    report_path: Path,
) -> dict[str, object]:
    summary = summarize_coverage(kb_rows, live_rows, backup_index)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    live_by_url = {(row.get("url") or "").strip(): row for row in live_rows}
    row_counts = Counter((row.get("source_url") or "").strip() for row in kb_rows)
    detail_rows = []
    for url in sorted(row_counts):
        if not url:
            continue
        live = live_by_url.get(url, {})
        backup = backup_index.get(url, {})
        detail_rows.append({
            "url": url,
            "row_count": row_counts[url],
            "traceability_status": live.get("traceability_status", "not_audited"),
            "http_status": live.get("http_status", ""),
            "content_type": live.get("content_type", ""),
            "is_pdf_source": "yes" if live and is_pdf_source(live) else "no",
            "backup_kind": backup.get("backup_kind", "none"),
            "has_local_pdf": "yes" if backup.get("has_local_pdf") else "no",
            "local_paths": " | ".join(str(path) for path in backup.get("paths", [])),
        })

    detail_path = output_dir / "source_backup_coverage.csv"
    with detail_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(detail_rows[0]))
        writer.writeheader()
        writer.writerows(detail_rows)

    generated_at = datetime.now(timezone.utc).isoformat()
    audit_date = datetime.now(timezone.utc).astimezone().date().isoformat()
    payload = {"generated_at": generated_at, **summary}
    (output_dir / "source_backup_coverage_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    missing_pdf_rows = [
        row for row in detail_rows
        if row["is_pdf_source"] == "yes" and row["has_local_pdf"] == "no"
    ]
    lines = [
        f"# 知识库来源链接与本地备份覆盖审计（{audit_date}）",
        "",
        f"- 生成时间（UTC）：`{generated_at}`",
        f"- 知识片段：**{summary['kb_rows']}** 条；唯一来源链接：**{summary['unique_source_urls']}** 个",
        f"- 本次实测可打开：**{summary['open_urls']}** 个；被站点/反爬拦截：**{summary['blocked_or_forbidden_urls']}** 个；网络错误：**{summary['network_error_urls']}** 个；异常 HTTP 状态：**{summary['bad_http_status_urls']}** 个；未审计：**{summary['not_audited_urls']}** 个；其他状态：**{summary['other_status_urls']}** 个（六项之和等于唯一来源链接总数）",
        f"- 有本地原件或归档证据：**{summary['urls_with_local_evidence']}** 个链接，覆盖 **{summary['rows_with_local_evidence']}** 条知识片段",
        f"- PDF 来源：**{summary['pdf_source_urls']}** 个；有本地 PDF 证据副本：**{summary['pdf_urls_with_local_pdf']}** 个；缺本地 PDF 证据：**{summary['pdf_urls_missing_local_pdf']}** 个",
        "",
        "## 结论口径",
        "",
        "1. `blocked_or_forbidden` 只表示自动化访问被站点策略拦截，不能直接判定链接失效；需要浏览器抽样或更换官方镜像复核。",
        "2. `network_error` 是当前网络下未完成验证的来源，不能算作已通过。",
        "3. `archive_replay`、官方规范化地址和机构镜像均保留在清单的 `backup_kind`/`attempted_url` 中；这些副本不能冒充原始 URL 的实时直连下载。",
        "4. 只有 `backup_kind=original` 才能称为原始 URL 直连原件；其余只能称为归档/镜像证据副本。",
        "",
        "## PDF 证据缺口（按影响片段数排序）",
        "",
        "| 影响片段 | 实测状态 | 来源链接 |",
        "|---:|---|---|",
    ]
    for row in sorted(missing_pdf_rows, key=lambda item: int(item["row_count"]), reverse=True):
        lines.append(f"| {row['row_count']} | {row['traceability_status']} | {row['url']} |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, default=REPO_ROOT / "knowledge_base_curated.csv")
    parser.add_argument(
        "--live-audit",
        type=Path,
        default=REPO_ROOT / "artifacts/kb_traceability_20260725/kb_source_url_audit.csv",
    )
    parser.add_argument(
        "--public-report",
        type=Path,
        default=REPO_ROOT / "artifacts/link_check_public_20260429/link_check_report.json",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=REPO_ROOT / "artifacts/web_ingest_public_20260429/raw",
    )
    parser.add_argument(
        "--archive-manifest",
        type=Path,
        default=REPO_ROOT / "artifacts/kb_source_archive_20260723/kb_source_archive_manifest_20260723.csv",
    )
    parser.add_argument(
        "--pdf-backup-manifest",
        type=Path,
        nargs="+",
        default=[
            REPO_ROOT / "artifacts/pdf_source_backups_20260725/pdf_backup_manifest_20260725.csv"
        ],
    )
    parser.add_argument(
        "--pdf-backup-dir",
        type=Path,
        nargs="+",
        default=[REPO_ROOT / "artifacts/pdf_source_backups_20260725/files"],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "artifacts/source_backup_coverage_20260725",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPO_ROOT / "docs/eval/source_backup_coverage_20260725.md",
    )
    args = parser.parse_args()

    kb_rows = read_csv(args.kb)
    live_rows = read_csv(args.live_audit)
    public_items = json.loads(args.public_report.read_text(encoding="utf-8"))["items"]
    archive_rows = read_csv(args.archive_manifest)
    pdf_backup_rows = [
        row
        for manifest_path in args.pdf_backup_manifest
        if manifest_path.exists()
        for row in read_csv(manifest_path)
    ]
    backup_index = build_backup_index(public_items, args.raw_dir, archive_rows, pdf_backup_rows)
    for pdf_backup_dir in args.pdf_backup_dir:
        add_pdf_backup_files_by_url_hash(backup_index, live_rows, pdf_backup_dir)
    summary = write_outputs(
        kb_rows,
        live_rows,
        backup_index,
        args.output_dir,
        args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
