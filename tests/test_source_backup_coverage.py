from pathlib import Path


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
