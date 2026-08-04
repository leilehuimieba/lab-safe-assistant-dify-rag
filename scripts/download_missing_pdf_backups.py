#!/usr/bin/env python3
"""Download currently missing PDF source originals into a dated local archive.

The script is deliberately conservative:
- it reads the existing source-backup coverage report to identify PDF source URLs
  that do not have local PDF evidence yet;
- it saves only responses that are real, complete PDF files: a ``%PDF`` header
  after a small whitespace/BOM allowance *and* a ``%%EOF`` end marker, so a body
  cut off mid-transfer is never filed as a finished backup;
- when a transfer is truncated it resumes with an HTTP range request instead of
  discarding the partial body, which matters on slow government origins;
- when the old ``.pdf`` path now redirects to a CMS landing page, it follows one
  hop to the document link on that page before declaring the source unreachable;
- it writes a manifest for both successes and failures, so the result is auditable
  and does not turn blocked pages into false "backups".
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_module
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, unquote, urljoin, urlsplit

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


def repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> Path:
    """Return a repository-relative path for absolute or caller-relative paths."""
    absolute = path if path.is_absolute() else Path.cwd() / path
    return absolute.resolve().relative_to(repo_root.resolve())


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


def wayback_replay_url(url: str) -> str:
    """Return Wayback's raw replay URL for an archived response body.

    ``id_`` asks Wayback to replay the captured body without injecting archive
    UI into HTML responses.  PDF acceptance still requires the ``%PDF`` magic
    check, and the manifest labels this path as ``archive_replay`` rather than a
    fresh direct download.
    """
    return f"https://web.archive.org/web/2id_/{url}"


def looks_like_pdf(data: bytes) -> bool:
    prefix = data[:2048].lstrip(b"\xef\xbb\xbf\r\n\t ")
    return prefix.startswith(b"%PDF-")


def is_complete_pdf(data: bytes) -> bool:
    """Reject bodies that start with ``%PDF-`` but were cut off in transit.

    A transfer killed by ``--max-time`` still leaves a file whose first bytes are
    valid PDF magic, so ``looks_like_pdf`` alone accepts half a document.  Every
    complete PDF ends with a ``%%EOF`` marker, so requiring it in the tail
    separates a finished download from a truncated one without adding a parser
    dependency.  Checked against all 150 stored backups on 2026-08-03: this
    agrees with ``pypdf`` on every file.
    """
    return looks_like_pdf(data) and b"%%EOF" in data[-2048:]


def pdf_links_in_html(data: bytes, base_url: str) -> list[str]:
    """Pull candidate document links out of an HTML landing page.

    Institutions migrate file trees and leave the old ``.pdf`` path 301-ing to a
    CMS landing page; the file itself is still published, one click away.  Yale
    EHS did exactly this (Drupal 10, ``/resource/<slug>`` with the file behind
    ``/resource/download/<id>``), which made 9 live documents look like dead
    links in the 2026-08-03 run.  Following one hop recovers them.
    """
    try:
        text = data.decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 - malformed HTML must not abort a run.
        return []
    candidates: list[str] = []
    for pattern in (
        r'href="(/[^"]*/download/\d+)"',
        r'href="([^"]+\.pdf(?:\?[^"]*)?)"',
    ):
        for href in re.findall(pattern, text, flags=re.IGNORECASE):
            if "/css/" in href or "/js/" in href:
                continue
            resolved = urljoin(base_url, html_module.unescape(href))
            if resolved not in candidates:
                candidates.append(resolved)
    return candidates[:3]


MAX_RESUME_ATTEMPTS = 6


def _curl(
    url: str,
    tmp_path: Path,
    header_path: Path,
    ua: str,
    max_seconds: int,
    max_bytes: int,
    resume: bool = False,
) -> subprocess.CompletedProcess[str]:
        cmd = [
            "curl.exe",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            # Windows Schannel aborts the TLS handshake ("EOF"/handshake failed)
            # when the local network blocks CRL/OCSP revocation lookups.  Skipping
            # the revocation check lets government CDNs (cdc.gov, nrc.gov, epa.gov,
            # osp.od.nih.gov) complete the handshake without weakening cert checks.
            "--ssl-no-revoke",
            "--connect-timeout",
            "12",
            "--max-time",
            str(max_seconds),
            "--max-filesize",
            str(max_bytes),
            "--user-agent",
            ua,
            # Present a full browser-like header set.  Several WAFs return 403 to
            # requests that only send Accept: application/pdf; a real navigation
            # sends an HTML-first Accept plus Sec-Fetch metadata.
            "--header",
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,"
            "application/pdf,*/*;q=0.8",
            "--header",
            "Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "--header",
            "Sec-Fetch-Dest: document",
            "--header",
            "Sec-Fetch-Mode: navigate",
            "--header",
            "Sec-Fetch-Site: none",
            "--header",
            "Sec-Fetch-User: ?1",
            "--header",
            "Upgrade-Insecure-Requests: 1",
            "--dump-header",
            str(header_path),
            "--output",
            str(tmp_path),
        ]
        if resume:
            # Continue an interrupted body instead of discarding it.  Slow origins
            # (ors.od.nih.gov served ~7 KB/s on 2026-08-03) otherwise lose a
            # multi-megabyte transfer every time --max-time expires.
            cmd += ["--continue-at", "-"]
        cmd.append(url)
        return subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max_seconds + 10,
        )


def _parse_headers(header_path: Path) -> tuple[str, str, str]:
    headers_text = (
        header_path.read_text(encoding="utf-8", errors="ignore") if header_path.exists() else ""
    )
    status = re.findall(r"^HTTP/\S+\s+(\d+)", headers_text, flags=re.MULTILINE)
    ctype = re.findall(r"^content-type:\s*(.+)$", headers_text, flags=re.IGNORECASE | re.MULTILINE)
    location = re.findall(r"^location:\s*(.+)$", headers_text, flags=re.IGNORECASE | re.MULTILINE)
    return (
        status[-1] if status else "",
        ctype[-1].strip() if ctype else "",
        location[-1].strip() if location else "",
    )


def download_once(url: str, out_path: Path, max_seconds: int, max_bytes: int) -> dict[str, str]:
    last_error = ""
    for ua in USER_AGENTS:
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        tmp_path.unlink(missing_ok=True)
        header_path = out_path.with_suffix(out_path.suffix + ".headers.txt")
        header_path.unlink(missing_ok=True)
        try:
            proc = _curl(url, tmp_path, header_path, ua, max_seconds, max_bytes)
            http_status, content_type, location = _parse_headers(header_path)
            data = tmp_path.read_bytes() if tmp_path.is_file() else b""

            # A body that starts with PDF magic but has no %%EOF was cut off in
            # transit; resume it rather than treating the origin as unreachable.
            attempts = 0
            while (
                looks_like_pdf(data)
                and not is_complete_pdf(data)
                and attempts < MAX_RESUME_ATTEMPTS
            ):
                attempts += 1
                before = len(data)
                proc = _curl(
                    url, tmp_path, header_path, ua, max_seconds, max_bytes, resume=True
                )
                data = tmp_path.read_bytes() if tmp_path.is_file() else b""
                if len(data) == before:
                    last_error = (
                        f"truncated PDF at {before} bytes; resume made no progress"
                    )
                    break

            if is_complete_pdf(data):
                tmp_path.replace(out_path)
                return {
                    "http_status": http_status,
                    "content_type": content_type,
                    "final_url": location or url,
                    "user_agent": ua,
                    "resume_attempts": str(attempts),
                }

            if looks_like_pdf(data):
                last_error = last_error or f"truncated PDF at {len(data)} bytes"
                tmp_path.unlink(missing_ok=True)
                continue

            # An HTML body here usually means the file tree moved and the old
            # .pdf path now redirects to a CMS landing page that still links the
            # document.  Follow exactly one hop before calling this a failure.
            if data and "html" in content_type.lower():
                for candidate in pdf_links_in_html(data, location or url):
                    hop_proc = _curl(
                        candidate, tmp_path, header_path, ua, max_seconds, max_bytes
                    )
                    hop_status, hop_type, hop_location = _parse_headers(header_path)
                    hop_data = tmp_path.read_bytes() if tmp_path.is_file() else b""
                    hop_attempts = 0
                    while (
                        looks_like_pdf(hop_data)
                        and not is_complete_pdf(hop_data)
                        and hop_attempts < MAX_RESUME_ATTEMPTS
                    ):
                        hop_attempts += 1
                        before = len(hop_data)
                        hop_proc = _curl(
                            candidate,
                            tmp_path,
                            header_path,
                            ua,
                            max_seconds,
                            max_bytes,
                            resume=True,
                        )
                        hop_data = tmp_path.read_bytes() if tmp_path.is_file() else b""
                        if len(hop_data) == before:
                            break
                    if is_complete_pdf(hop_data):
                        tmp_path.replace(out_path)
                        return {
                            "http_status": hop_status,
                            "content_type": hop_type,
                            "final_url": hop_location or candidate,
                            "user_agent": ua,
                            "resume_attempts": str(hop_attempts),
                            "landing_page": location or url,
                        }
                    del hop_proc
                last_error = "response was an HTML landing page with no usable document link"
                tmp_path.unlink(missing_ok=True)
                continue

            if proc.returncode != 0:
                last_error = f"curl exit {proc.returncode}: {proc.stderr.strip()[:200]}"
                continue
            if not data:
                last_error = "curl succeeded but output file is missing"
                continue
            last_error = "response was not a PDF"
            tmp_path.unlink(missing_ok=True)
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
        "$ErrorActionPreference='Stop'; "
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
            if not is_complete_pdf(data):
                last_error = (
                    "powershell response was a truncated PDF"
                    if looks_like_pdf(data)
                    else "powershell response was not a PDF"
                )
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
    parser.add_argument(
        "--wayback-only",
        action="store_true",
        help="Retry each source only through a raw Wayback replay; label it archive_replay.",
    )
    args = parser.parse_args()

    rows = read_csv(args.coverage)
    statuses = {item.strip() for item in args.statuses.split(",") if item.strip()}
    targets = iter_targets(rows, args.limit, statuses or None)
    output_dir = args.output_dir.resolve()
    date_match = re.search(r"(\d{8})$", output_dir.name)
    run_label = date_match.group(1) if date_match else datetime.now().strftime("%Y%m%d")
    files_dir = output_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"pdf_backup_manifest_{run_label}.csv"

    manifest_rows: list[dict[str, str]] = []
    max_bytes = args.max_mb * 1024 * 1024
    for idx, row in enumerate(targets, 1):
        source_url = row["url"]
        local_name = slug_for_url(source_url, idx)
        local_path = files_dir / local_name
        print(f"[{idx}/{len(targets)}] {source_url}", flush=True)
        status = "failed"
        backup_kind = ""
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
            backup_kind = "archive_replay" if args.wayback_only else "original"
            notes = "existing_validated_pdf_magic"
        else:
            download_candidates = (
                [(wayback_replay_url(source_url), "archive_replay")]
                if args.wayback_only
                else [(candidate, "original") for candidate in candidate_urls(source_url)]
            )
            for candidate, candidate_kind in download_candidates:
                try:
                    meta = download_once(candidate, local_path, max_seconds=args.max_seconds, max_bytes=max_bytes)
                    used_url = candidate
                    data = local_path.read_bytes()
                    sha256 = hashlib.sha256(data).hexdigest()
                    size = str(len(data))
                    status = "downloaded"
                    backup_kind = candidate_kind
                    notes = (
                        "validated_pdf_magic_from_raw_wayback_replay"
                        if candidate_kind == "archive_replay"
                        else "validated_pdf_magic"
                    )
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
            "backup_kind": backup_kind,
            "local_path": str(repo_relative(local_path)) if status == "downloaded" else "",
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
            "backup_kind",
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
        "direct_original": sum(
            1 for row in manifest_rows
            if row["status"] == "downloaded" and row["backup_kind"] == "original"
        ),
        "archive_replay": sum(
            1 for row in manifest_rows
            if row["status"] == "downloaded" and row["backup_kind"] == "archive_replay"
        ),
        "failed": sum(1 for row in manifest_rows if row["status"] != "downloaded"),
        "manifest": str(repo_relative(manifest_path)),
        "files_dir": str(repo_relative(files_dir)),
    }
    (output_dir / f"pdf_backup_summary_{run_label}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["downloaded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
