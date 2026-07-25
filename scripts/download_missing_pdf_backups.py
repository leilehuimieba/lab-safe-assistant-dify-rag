#!/usr/bin/env python3
"""Download currently missing PDF source originals into a dated local archive.

The script is deliberately conservative:
- it reads the existing source-backup coverage report to identify PDF source URLs
  that do not have local PDF evidence yet;
- it saves only responses that look like real PDF files (``%PDF`` header after a
  small whitespace/BOM allowance);
- it writes a manifest for both successes and failures, so the result is auditable
  and does not turn blocked pages into false "backups".
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COVERAGE = (
    REPO_ROOT / "artifacts/source_backup_coverage_20260725/source_backup_coverage.csv"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts/pdf_source_backups_20260725"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "curl/8.0.1",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def is_missing_pdf(row: dict[str, str]) -> bool:
    return row.get("is_pdf_source") == "yes" and row.get("has_local_pdf") != "yes"


def slug_for_url(url: str, index: int) -> str:
    parsed = urlsplit(url)
    host = re.sub(r"[^A-Za-z0-9.-]+", "_", parsed.netloc).strip("._") or "source"
    leaf = Path(unquote(parsed.path)).name or "document.pdf"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", leaf).strip("._")
    if not stem.lower().endswith(".pdf"):
        stem += ".pdf"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{index:03d}_{host}_{digest}_{stem}"[:180]


def candidate_urls(url: str) -> list[str]:
    """Return small, same-resource URL variants.

    This avoids broad web search in the downloader itself; replacement/mirror
    sources should be recorded by a human-reviewed follow-up manifest.
    """
    parsed = urlsplit(url)
    candidates = [url]
    if parsed.scheme == "http":
        candidates.append("https://" + url[len("http://") :])
    elif parsed.scheme == "https":
        candidates.append("http://" + url[len("https://") :])

    # Some legacy URLs contain literal spaces. Keep path quoting conservative.
    quoted_path = quote(unquote(parsed.path), safe="/:@%._+-")
    if quoted_path != parsed.path:
        rebuilt = parsed._replace(path=quoted_path).geturl()
        candidates.append(rebuilt)

    deduped: list[str] = []
    seen = set()
    for item in candidates:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def looks_like_pdf(data: bytes) -> bool:
    prefix = data[:2048].lstrip(b"\xef\xbb\xbf\r\n\t ")
    return prefix.startswith(b"%PDF-")


def download_once(url: str, out_path: Path, max_seconds: int, max_bytes: int) -> dict[str, str]:
    last_error = ""
    for ua in USER_AGENTS:
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        tmp_path.unlink(missing_ok=True)
        header_path = out_path.with_suffix(out_path.suffix + ".headers.txt")
        header_path.unlink(missing_ok=True)
        cmd = [
            "curl.exe",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--connect-timeout",
            "12",
            "--max-time",
            str(max_seconds),
            "--max-filesize",
            str(max_bytes),
            "--user-agent",
            ua,
            "--header",
            "Accept: application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
            "--header",
            "Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "--dump-header",
            str(header_path),
            "--output",
            str(tmp_path),
            url,
        ]
        try:
            proc = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max_seconds + 10,
            )
            headers_text = header_path.read_text(encoding="utf-8", errors="ignore") if header_path.exists() else ""
            status_matches = re.findall(r"^HTTP/\\S+\\s+(\\d+)", headers_text, flags=re.MULTILINE)
            type_matches = re.findall(r"^content-type:\\s*(.+)$", headers_text, flags=re.IGNORECASE | re.MULTILINE)
            location_matches = re.findall(r"^location:\\s*(.+)$", headers_text, flags=re.IGNORECASE | re.MULTILINE)
            if proc.returncode != 0:
                last_error = f"curl exit {proc.returncode}: {proc.stderr.strip()[:200]}"
                continue
            if not tmp_path.is_file():
                last_error = "curl succeeded but output file is missing"
                continue
            data = tmp_path.read_bytes()
            if not looks_like_pdf(data):
                last_error = "response was not a PDF"
                tmp_path.unlink(missing_ok=True)
                continue
            tmp_path.replace(out_path)
            return {
                "http_status": status_matches[-1] if status_matches else "",
                "content_type": type_matches[-1].strip() if type_matches else "",
                "final_url": location_matches[-1].strip() if location_matches else url,
                "user_agent": ua,
            }
        except (subprocess.TimeoutExpired, OSError, RuntimeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        finally:
            tmp_path.unlink(missing_ok=True)
            header_path.unlink(missing_ok=True)

    # Windows PowerShell/.NET sometimes succeeds where the bundled curl.exe
    # fails because the TLS stack and enterprise certificate handling differ.
    # Keep this as a conservative fallback and still require PDF magic before
    # accepting the file.
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.unlink(missing_ok=True)
    ps_script = (
        "& { param($Url, $OutFile, $TimeoutSeconds) "
        "$ProgressPreference='SilentlyContinue'; "
        "[Net.ServicePointManager]::SecurityProtocol = "
        "[Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13; "
        "Invoke-WebRequest -Uri $Url -OutFile $OutFile "
        "-MaximumRedirection 5 -TimeoutSec $TimeoutSeconds -UseBasicParsing "
        "-Headers @{'User-Agent'='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'; "
        "'Accept'='application/pdf,application/octet-stream;q=0.9,*/*;q=0.8'} }"
    )
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps_script,
                url,
                str(tmp_path),
                str(max_seconds),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max_seconds + 15,
        )
        if proc.returncode != 0:
            last_error = f"powershell exit {proc.returncode}: {proc.stderr.strip()[:200]}"
        elif not tmp_path.is_file():
            last_error = "powershell succeeded but output file is missing"
        elif tmp_path.stat().st_size > max_bytes:
            last_error = "powershell output exceeded max size"
        else:
            data = tmp_path.read_bytes()
            if not looks_like_pdf(data):
                last_error = "powershell response was not a PDF"
            else:
                tmp_path.replace(out_path)
                return {
                    "http_status": "",
                    "content_type": "application/pdf",
                    "final_url": url,
                    "user_agent": "PowerShell Invoke-WebRequest",
                }
    except (subprocess.TimeoutExpired, OSError, RuntimeError) as exc:
        last_error = f"{type(exc).__name__}: {exc}"
    finally:
        tmp_path.unlink(missing_ok=True)
    raise RuntimeError(last_error or "download failed")


def iter_targets(
    rows: Iterable[dict[str, str]],
    limit: int | None,
    statuses: set[str] | None,
) -> list[dict[str, str]]:
    targets = [row for row in rows if is_missing_pdf(row)]
    if statuses:
        targets = [row for row in targets if (row.get("traceability_status") or "") in statuses]
    targets.sort(key=lambda row: int(row.get("row_count") or 0), reverse=True)
    return targets if limit is None else targets[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--statuses",
        default="",
        help="Comma-separated traceability statuses to include, e.g. open,network_error.",
    )
    parser.add_argument("--max-seconds", type=int, default=45)
    parser.add_argument("--max-mb", type=int, default=80)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    rows = read_csv(args.coverage)
    statuses = {item.strip() for item in args.statuses.split(",") if item.strip()}
    targets = iter_targets(rows, args.limit, statuses or None)
    files_dir = args.output_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "pdf_backup_manifest_20260725.csv"

    manifest_rows: list[dict[str, str]] = []
    max_bytes = args.max_mb * 1024 * 1024
    for idx, row in enumerate(targets, 1):
        source_url = row["url"]
        local_name = slug_for_url(source_url, idx)
        local_path = files_dir / local_name
        print(f"[{idx}/{len(targets)}] {source_url}", flush=True)
        status = "failed"
        notes = ""
        meta = {
            "http_status": "",
            "content_type": "",
            "final_url": "",
            "user_agent": "",
        }
        sha256 = ""
        size = ""
        used_url = ""
        if local_path.is_file() and looks_like_pdf(local_path.read_bytes()[:2048]):
            data = local_path.read_bytes()
            sha256 = hashlib.sha256(data).hexdigest()
            size = str(len(data))
            status = "downloaded"
            notes = "existing_validated_pdf_magic"
        else:
            for candidate in candidate_urls(source_url):
                try:
                    meta = download_once(candidate, local_path, max_seconds=args.max_seconds, max_bytes=max_bytes)
                    used_url = candidate
                    data = local_path.read_bytes()
                    sha256 = hashlib.sha256(data).hexdigest()
                    size = str(len(data))
                    status = "downloaded"
                    notes = "validated_pdf_magic"
                    break
                except Exception as exc:  # noqa: BLE001 - manifest must capture all failures.
                    notes = str(exc)[:300]
                    continue

        manifest_rows.append({
            "source_url": source_url,
            "row_count": row.get("row_count", ""),
            "traceability_status": row.get("traceability_status", ""),
            "attempted_url": used_url,
            "final_url": meta.get("final_url", ""),
            "http_status": meta.get("http_status", ""),
            "content_type": meta.get("content_type", ""),
            "status": status,
            "local_path": str(local_path.relative_to(REPO_ROOT)) if status == "downloaded" else "",
            "sha256": sha256,
            "size_bytes": size,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
        })
        time.sleep(args.sleep)

    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = [
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
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "targets": len(targets),
        "downloaded": sum(1 for row in manifest_rows if row["status"] == "downloaded"),
        "failed": sum(1 for row in manifest_rows if row["status"] != "downloaded"),
        "manifest": str(manifest_path.relative_to(REPO_ROOT)),
        "files_dir": str(files_dir.relative_to(REPO_ROOT)),
    }
    (args.output_dir / "pdf_backup_summary_20260725.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["downloaded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
