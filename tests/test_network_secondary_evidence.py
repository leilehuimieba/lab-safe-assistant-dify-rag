from scripts.recheck_network_errors_with_archive import (
    classify_evidence,
    needs_secondary_evidence,
)


def test_only_unresolved_manual_reader_rows_need_secondary_evidence():
    assert needs_secondary_evidence(
        {"manual_reader_status": "web_reader_error_or_blocked"}
    )
    assert not needs_secondary_evidence(
        {"manual_reader_status": "web_reader_open_pdf"}
    )


def test_evidence_classifier_requires_real_pdf_or_substantial_html():
    assert classify_evidence(b"%PDF-1.7\ncontent", "application/pdf") == "pdf"
    assert classify_evidence(
        b"<!doctype html><html><body>" + b"x" * 500 + b"</body></html>",
        "text/html; charset=UTF-8",
    ) == "html"
    assert classify_evidence(b"<html>blocked</html>", "text/html") == ""
