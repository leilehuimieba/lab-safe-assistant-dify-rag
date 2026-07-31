from pathlib import Path
import hashlib


def test_build_backup_index_distinguishes_originals_and_mirrors(tmp_path: Path):
    from scripts.audit_source_backup_coverage import build_backup_index

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "PDF-1_manual.pdf").write_bytes(b"%PDF-test")
    archived = tmp_path / "archived.html"
    archived.write_text("cached", encoding="utf-8")

    public_items = [{"id": "PDF-1", "url": "https://example.edu/manual.pdf"}]
    archive_rows = [
        {
            "original_citation_url": "https://blocked.example.edu/page",
            "mirror_url": "https://mirror.example.edu/page",
            "local_original_path": str(archived),
            "local_markdown_path": "",
        }
    ]

    index = build_backup_index(public_items, raw_dir, archive_rows)

    assert index["https://example.edu/manual.pdf"]["backup_kind"] == "original"
    assert index["https://example.edu/manual.pdf"]["has_local_pdf"] is True
    assert index["https://blocked.example.edu/page"]["backup_kind"] == "mirror"
    assert index["https://blocked.example.edu/page"]["has_local_pdf"] is False


def test_summarize_coverage_counts_unique_urls_rows_and_pdf_backups():
    from scripts.audit_source_backup_coverage import summarize_coverage

    kb_rows = [
        {"source_url": "https://example.edu/manual.pdf"},
        {"source_url": "https://example.edu/manual.pdf"},
        {"source_url": "https://example.edu/page"},
    ]
    live_rows = [
        {
            "url": "https://example.edu/manual.pdf",
            "traceability_status": "open",
            "content_type": "application/pdf",
        },
        {
            "url": "https://example.edu/page",
            "traceability_status": "network_error",
            "content_type": "text/html",
        },
    ]
    backup_index = {
        "https://example.edu/manual.pdf": {
            "backup_kind": "original",
            "has_local_pdf": True,
            "paths": ["manual.pdf"],
        }
    }

    summary = summarize_coverage(kb_rows, live_rows, backup_index)

    assert summary["unique_source_urls"] == 2
    assert summary["rows_with_local_evidence"] == 2
    assert summary["pdf_source_urls"] == 1
    assert summary["pdf_urls_with_local_pdf"] == 1
    assert summary["network_error_urls"] == 1


def test_summarize_coverage_status_breakdown_adds_up_to_unique_urls():
    """Every audited status must appear in the summary.

    ``bad_http_status`` used to be dropped, so the published breakdown summed to
    714 against 717 unique URLs.
    """
    from scripts.audit_source_backup_coverage import summarize_coverage

    statuses = ["open", "blocked_or_forbidden", "network_error", "bad_http_status", "weird_new_status"]
    kb_rows = [{"source_url": f"https://example.edu/{name}"} for name in statuses]
    kb_rows.append({"source_url": "https://example.edu/never-audited"})
    live_rows = [
        {"url": f"https://example.edu/{name}", "traceability_status": name, "content_type": "text/html"}
        for name in statuses
    ]

    summary = summarize_coverage(kb_rows, live_rows, {})

    assert summary["unique_source_urls"] == 6
    assert summary["bad_http_status_urls"] == 1
    assert summary["not_audited_urls"] == 1
    assert summary["other_status_urls"] == 1
    assert summary["status_counts"]["weird_new_status"] == 1
    breakdown = sum(summary[key] for key in (
        "open_urls",
        "blocked_or_forbidden_urls",
        "network_error_urls",
        "bad_http_status_urls",
        "not_audited_urls",
        "other_status_urls",
    ))
    assert breakdown == summary["unique_source_urls"]


def test_published_20260731_summary_breakdown_matches_detail_csv():
    """The shipped 2026-07-31 artifacts must stay internally consistent."""
    import csv
    import json
    from collections import Counter

    repo_root = Path(__file__).resolve().parents[1]
    detail_path = repo_root / "artifacts/source_backup_coverage_20260731/source_backup_coverage.csv"
    summary_path = repo_root / "artifacts/source_backup_coverage_20260731/source_backup_coverage_summary.json"
    if not detail_path.is_file() or not summary_path.is_file():
        import pytest

        pytest.skip("2026-07-31 coverage artifacts not present")

    with detail_path.open("r", encoding="utf-8-sig", newline="") as handle:
        detail_rows = list(csv.DictReader(handle))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(detail_rows) == summary["unique_source_urls"]
    assert Counter(row["traceability_status"] for row in detail_rows) == summary["status_counts"]
    assert sum(summary["status_counts"].values()) == summary["unique_source_urls"]


def test_add_pdf_backup_files_by_url_hash_indexes_downloaded_pdfs(tmp_path: Path):
    from scripts.audit_source_backup_coverage import add_pdf_backup_files_by_url_hash

    source_url = "https://example.edu/manual.pdf"
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:10]
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf_path = pdf_dir / f"001_example.edu_{digest}_manual.pdf"
    pdf_path.write_bytes(b"%PDF-test")

    backup_index = {}
    live_rows = [
        {
            "url": source_url,
            "traceability_status": "open",
            "content_type": "application/pdf",
        }
    ]

    add_pdf_backup_files_by_url_hash(backup_index, live_rows, pdf_dir)

    assert backup_index[source_url]["backup_kind"] == "original"
    assert backup_index[source_url]["has_local_pdf"] is True
    assert str(pdf_path) in backup_index[source_url]["paths"]


def test_archive_replay_pdf_is_evidence_but_not_direct_original(tmp_path: Path):
    from scripts.audit_source_backup_coverage import build_backup_index

    pdf_path = tmp_path / "osha_snapshot.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nsnapshot")
    url = "https://www.osha.gov/example.pdf"

    index = build_backup_index(
        [],
        tmp_path,
        [],
        [
            {
                "source_url": url,
                "status": "downloaded",
                "backup_kind": "archive_replay",
                "local_path": str(pdf_path),
            }
        ],
    )

    assert index[url]["backup_kind"] == "archive_replay"
    assert index[url]["has_local_pdf"] is True
