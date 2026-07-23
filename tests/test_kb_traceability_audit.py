from pathlib import Path


def test_row_audit_flags_traceability_and_metadata_issues(tmp_path: Path) -> None:
    from scripts.audit_kb_traceability import audit_rows

    rows = [
        {
            "id": "KB-1",
            "title": "ok",
            "category": "化学",
            "subcategory": "储存",
            "risk_level": "3",
            "source_title": "Source A",
            "source_org": "Org A",
            "source_url": "https://example.edu/a",
            "references": "Source A | https://example.edu/a",
        },
        {
            "id": "KB-2",
            "title": "bad risk",
            "category": "废弃物",
            "subcategory": "",
            "risk_level": "40 CFR Part 262",
            "source_title": "Source B",
            "source_org": "Org B",
            "source_url": "https://example.edu/b",
            "references": "待补充",
        },
        {
            "id": "KB-3",
            "title": "missing source",
            "category": "生物",
            "subcategory": "灭菌",
            "risk_level": "",
            "source_title": "",
            "source_org": "Org C",
            "source_url": "",
            "references": "",
        },
    ]

    audit = audit_rows(rows)

    assert audit["row_count"] == 3
    assert audit["missing_source_url_count"] == 1
    assert audit["invalid_risk_level_count"] == 1
    assert audit["missing_risk_level_count"] == 1
    assert audit["missing_subcategory_count"] == 1
    assert audit["missing_references_count"] == 1
    assert audit["references_placeholder_count"] == 1
    assert audit["references_without_source_title_count"] == 1
    assert audit["references_without_source_org_count"] == 2
    assert audit["references_without_source_url_count"] == 1
    assert audit["unique_source_url_count"] == 2
    assert audit["rows_by_source_url"]["https://example.edu/a"] == 1
    problem_by_id = {row["id"]: row["issues"] for row in audit["problem_rows"]}
    assert "references_without_source_org" in problem_by_id["KB-1"]
    assert "references_without_source_title" in problem_by_id["KB-2"]


def test_summary_payload_uses_url_items_instead_of_url_object_keys(tmp_path: Path) -> None:
    from scripts.audit_kb_traceability import build_summary_payload

    audit = {
        "row_count": 2,
        "problem_rows": [],
        "rows_by_source_url": {
            "https://www.osha.gov/sites/default/files/publications/OSHAFACTSHEET.pdf": 1,
            "https://www.osha.gov/sites/default/files/publications/OSHAfactsheet.pdf": 1,
        },
    }

    payload = build_summary_payload(audit, tmp_path / "kb.csv", ["id"], None)

    assert "rows_by_source_url" not in payload
    assert payload["rows_by_source_url_items"] == [
        {"source_url": "https://www.osha.gov/sites/default/files/publications/OSHAFACTSHEET.pdf", "row_count": 1},
        {"source_url": "https://www.osha.gov/sites/default/files/publications/OSHAfactsheet.pdf", "row_count": 1},
    ]


def test_url_result_classification_distinguishes_open_blocked_and_dead() -> None:
    from scripts.audit_kb_traceability import classify_url_result

    assert classify_url_result({"status": "ok", "http_status": 200}) == "open"
    assert classify_url_result({"status": "bad_status", "http_status": 403}) == "blocked_or_forbidden"
    assert classify_url_result({"status": "bad_status", "http_status": 404}) == "dead_or_moved"
    assert classify_url_result({"status": "error", "error": "ConnectTimeout"}) == "network_error"


def test_check_url_retries_with_browser_user_agent(monkeypatch) -> None:
    from scripts import audit_kb_traceability

    class FakeResponse:
        def __init__(self, status_code: int, body: bytes) -> None:
            self.status_code = status_code
            self.url = "https://example.edu/page"
            self.headers = {"content-type": "text/html"}
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def iter_content(self, chunk_size: int):
            yield self._body

    calls = []

    def fake_get(url, timeout, headers, stream, allow_redirects):
        calls.append(headers["User-Agent"])
        if len(calls) == 1:
            return FakeResponse(404, b"not found")
        return FakeResponse(200, b"<html>ok</html>")

    monkeypatch.setattr(audit_kb_traceability.requests, "get", fake_get)

    result = audit_kb_traceability.check_url("https://example.edu/page", timeout=1)

    assert result["status"] == "ok"
    assert result["http_status"] == 200
    assert result["attempt"] == 2
    assert calls[0] == audit_kb_traceability.USER_AGENT
    assert calls[1] == audit_kb_traceability.BROWSER_USER_AGENT


def test_check_url_can_ignore_proxy_environment(monkeypatch) -> None:
    from scripts import audit_kb_traceability

    sessions = []

    class FakeResponse:
        status_code = 200
        url = "https://example.edu/page"
        headers = {"content-type": "text/html"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def iter_content(self, chunk_size: int):
            yield b"ok"

    class FakeSession:
        def __init__(self) -> None:
            self.trust_env = True
            sessions.append(self)

        def get(self, url, timeout, headers, stream, allow_redirects):
            return FakeResponse()

    monkeypatch.setattr(audit_kb_traceability.requests, "Session", FakeSession)

    result = audit_kb_traceability.check_url("https://example.edu/page", timeout=1, trust_env=False)

    assert result["status"] == "ok"
    assert sessions
    assert sessions[0].trust_env is False


def test_metadata_fix_moves_legal_citation_out_of_risk_and_fills_references() -> None:
    from scripts.fix_kb_metadata_quality import normalize_row

    row = {
        "id": "KB-PHASE4-0720",
        "title": "RCRA危险废物产生者分类与管理要求",
        "category": "废弃物",
        "subcategory": "",
        "risk_level": "40 CFR Part 262; 40 CFR 262.14-262.17",
        "legal_notes": "",
        "references": "",
        "source_title": "Resource Conservation and Recovery Act Overview",
        "source_url": "https://www.epa.gov/rcra",
        "reviewer": "auto-ingest-phase4; pending human review",
    }

    updated, changes = normalize_row(row)

    assert updated["risk_level"] == "4"
    assert updated["subcategory"] == "危废处置"
    assert "40 CFR Part 262" in updated["legal_notes"]
    assert "Resource Conservation and Recovery Act Overview" in updated["references"]
    assert "https://www.epa.gov/rcra" in updated["references"]
    assert {
        "risk_level_legal_citation_moved",
        "risk_level_inferred",
        "subcategory_inferred",
        "references_filled",
    }.issubset(set(changes))


def test_metadata_fix_infers_high_risk_for_hf_without_overwriting_reviewed_fields() -> None:
    from scripts.fix_kb_metadata_quality import normalize_row

    row = {
        "id": "KB-X",
        "title": "氢氟酸泄漏应急处理",
        "category": "化学",
        "subcategory": "",
        "risk_level": "",
        "legal_notes": "existing note",
        "references": "existing ref",
        "source_title": "HF Guide",
        "source_url": "https://example.edu/hf",
        "reviewer": "manual reviewer",
    }

    updated, changes = normalize_row(row)

    assert updated["risk_level"] == "5"
    assert updated["subcategory"] == "化学应急"
    assert updated["legal_notes"] == "existing note"
    assert updated["references"].startswith("existing ref")
    assert "https://example.edu/hf" in updated["references"]
    assert "references_source_url_appended" in changes


def test_metadata_fix_replaces_reference_placeholder_with_current_source() -> None:
    from scripts.fix_kb_metadata_quality import normalize_row

    row = {
        "id": "KB-PLACEHOLDER",
        "title": "占位引用",
        "category": "通用",
        "subcategory": "制度",
        "risk_level": "2",
        "legal_notes": "",
        "references": "待补充",
        "source_title": "Official Manual",
        "source_org": "Official Org",
        "source_url": "https://example.edu/manual",
        "reviewer": "auto",
    }

    updated, changes = normalize_row(row)

    assert "待补充" not in updated["references"]
    assert "Official Manual" in updated["references"]
    assert "https://example.edu/manual" in updated["references"]
    assert "references_placeholder_replaced" in changes


def test_metadata_fix_appends_source_title_and_org_to_references() -> None:
    from scripts.fix_kb_metadata_quality import normalize_row

    row = {
        "id": "KB-STRICT-REF",
        "title": "引用缺少机构",
        "category": "通用",
        "subcategory": "制度",
        "risk_level": "2",
        "legal_notes": "",
        "references": "https://example.edu/manual",
        "source_title": "Official Manual",
        "source_org": "Official Org",
        "source_url": "https://example.edu/manual",
        "reviewer": "auto",
    }

    updated, changes = normalize_row(row)

    assert "Official Manual" in updated["references"]
    assert "Official Org" in updated["references"]
    assert "https://example.edu/manual" in updated["references"]
    assert "references_source_title_appended" in changes
    assert "references_source_org_appended" in changes


def test_url_replacement_can_update_source_metadata() -> None:
    from scripts.apply_kb_url_replacements import canonicalize_url

    replacement = canonicalize_url("https://ehs.stonybrook.edu/resources/our-policies/Laboratory%20Hood%20Safety.pdf")

    assert replacement is not None
    assert replacement["url"].endswith("EHS_Policy_4.5_Laboratory_Chemical_Fume_Hood_Safety_Program.pdf")
    assert replacement["source_title"] == "Stony Brook University Laboratory Chemical Fume Hood Safety Program"
    assert replacement["source_org"] == "Stony Brook University Environmental Health and Safety"
