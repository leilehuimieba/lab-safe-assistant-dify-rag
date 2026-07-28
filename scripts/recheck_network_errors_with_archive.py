#!/usr/bin/env python3
"""Add independent content evidence for unresolved historical network errors.

The current live status is deliberately preserved.  A successful raw Wayback
replay proves that a historical source body exists and can be inspected locally;
it does not prove that the original URL is reachable today.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    REPO_ROOT / "artifacts/source_recheck_20260728/network_error_recheck_31.csv"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts/source_recheck_20260728/secondary_evidence"


def needs_secondary_evidence(row: dict[str, str]) -> bool:
    return (row.get("manual_reader_status") or "").strip() == (
        "web_reader_error_or_blocked"
    )


def classify_evidence(data: bytes, content_type: str) -> str:
    prefix = data[:2048].lstrip(b"\xef\xbb\xbf\r\n\t ")
    normalized_type = (content_type or "").lower()
    if prefix.startswith(b"%PDF-"):
        return "pdf"
    if (
        len(data) >= 256
        and ("text/html" in normalized_type or b"<html" in prefix.lower())
        and b"wayback machine has not archived that url" not in data[:10000].lower()
    ):
        return "html"
    return ""


def replay_url(source_url: str) -> str:
    return f"https://web.archive.org/web/2id_/{source_url}"


def evidence_filename(source_url: str, index: int, kind: str) -> str:
    parsed = urlsplit(source_url)
    leaf = Path(unquote(parsed.path)).name or "index"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", leaf).strip("._") or "source"
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:10]
    suffix = ".pdf" if kind == "pdf" else ".html"
    if stem.lower().endswith((".pdf", ".html", ".htm")):
        stem = stem.rsplit(".", 1)[0]
    return f"{index:03d}_{parsed.netloc}_{digest}_{stem}{suffix}"[:190]


def repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--max-mb", type=int, default=100)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    targets = [row for row in source_rows if needs_secondary_evidence(row)]

    output_dir = args.output_dir.resolve()
    files_dir = output_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/126.0"
            )
        }
    )
    max_bytes = args.max_mb * 1024 * 1024
    results: list[dict[str, str]] = []

    for index, row in enumerate(targets, 1):
        source_url = (row.get("url") or "").strip()
        evidence_url = replay_url(source_url)
        print(f"[{index}/{len(targets)}] {source_url}", flush=True)
        result = {
            "source_url": source_url,
            "row_count": row.get("row_count", ""),
            "live_recheck_status": row.get("new_status", ""),
            "manual_reader_status": row.get("manual_reader_status", ""),
            "evidence_url": evidence_url,
            "final_url": "",
            "http_status": "",
            "content_type": "",
            "evidence_kind": "",
            "content_verified": "no",
            "local_path": "",
            "sha256": "",
            "size_bytes": "",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "notes": "",
        }
        try:
            with session.get(
                evidence_url,
                timeout=(15, args.timeout),
                stream=True,
            ) as response:
                result["final_url"] = response.url
                result["http_status"] = str(response.status_code)
                result["content_type"] = response.headers.get("Content-Type", "")
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        raise ValueError(
                            f"response exceeds {args.max_mb} MiB limit"
                        )
                data = bytes(body)
            kind = classify_evidence(data, result["content_type"])
            if not kind:
                raise ValueError("response is not a validated PDF or substantial HTML body")
            local_path = files_dir / evidence_filename(source_url, index, kind)
            local_path.write_bytes(data)
            result["evidence_kind"] = f"wayback_{kind}"
            result["content_verified"] = "yes"
            result["local_path"] = repo_relative(local_path)
            result["sha256"] = hashlib.sha256(data).hexdigest()
            result["size_bytes"] = str(len(data))
            result["notes"] = (
                "historical content evidence only; live URL status remains unchanged"
            )
        except Exception as exc:  # noqa: BLE001 - every failure belongs in the audit.
            result["notes"] = f"{type(exc).__name__}: {exc}"[:500]
        results.append(result)
    session.close()

    manifest_path = output_dir / "network_error_secondary_evidence_25.csv"
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]) if results else [])
        if results:
            writer.writeheader()
            writer.writerows(results)

    verified = sum(row["content_verified"] == "yes" for row in results)
    official_index_path = output_dir / "network_error_official_index_evidence_10.csv"
    official_index_count = 0
    if official_index_path.is_file():
        with official_index_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            official_index_rows = list(csv.DictReader(handle))
        official_index_count = sum(
            (row.get("evidence_verified") or "").strip().lower() == "yes"
            for row in official_index_rows
        )
    secondary_total = min(len(results), verified + official_index_count)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_count": len(results),
        "content_verified_count": verified,
        "unresolved_count": len(results) - verified,
        "pdf_evidence_count": sum(
            row["evidence_kind"] == "wayback_pdf" for row in results
        ),
        "html_evidence_count": sum(
            row["evidence_kind"] == "wayback_html" for row in results
        ),
        "manifest": repo_relative(manifest_path),
        "scope_note": (
            "Archive replay is independent historical content evidence and does "
            "not replace the current live network_error status."
        ),
        "archive_local_content_count": verified,
        "official_index_evidence_count": official_index_count,
        "secondary_evidence_total": secondary_total,
        "remaining_without_secondary_evidence": len(results) - secondary_total,
        "official_index_manifest": (
            repo_relative(official_index_path)
            if official_index_path.is_file()
            else ""
        ),
    }
    summary_path = output_dir / "network_error_secondary_evidence_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        "# 25 个历史 network_error 二次证据复核",
        "",
        f"- 生成时间（UTC）：`{summary['generated_at']}`",
        f"- 待补二次内容证据：**{summary['target_count']}** 个",
        f"- 已形成可校验本地归档内容证据：**{summary['content_verified_count']}** 个",
        f"- 其中 PDF：**{summary['pdf_evidence_count']}** 个；HTML：**{summary['html_evidence_count']}** 个",
        f"- 官方域名搜索索引/官方现行替代页证据：**{official_index_count}** 个",
        f"- 仍无二次证据：**{summary['remaining_without_secondary_evidence']}** 个",
        "",
        "## 证据边界",
        "",
        "- 本轮使用 Wayback `id_` 原始响应回放，保存文件、SHA-256、大小、抓取时间和最终回放 URL。",
        "- Wayback 无存档时，可用官方域名搜索索引、现行官方替代页或官方支持交叉引用补证；该层不冒充本地原件。",
        "- 该证据用于证明历史引用内容可回溯，不把归档回放误写成当前官网可访问。",
        "- 原审计的 `network_error` 状态保持不变；当前可用性仍需以后续官网直连复测为准。",
        "",
        f"明细：`{summary['manifest']}`",
        f"官方索引补证：`{summary['official_index_manifest'] or '未提供'}`",
    ]
    (output_dir / "network_error_secondary_evidence_25.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if secondary_total == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
