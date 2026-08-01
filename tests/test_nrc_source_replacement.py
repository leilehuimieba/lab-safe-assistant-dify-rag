import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
KB_PATH = REPO_ROOT / "knowledge_base_curated.csv"
TARGET_IDS = {"KB-RECO-0090", "KB-RECO-0099", "KB-RECO-0189"}
OLD_NRC_URL = "https://www.nrc.gov/docs/ML2014/ML20147A696.pdf"


def load_target_rows() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    with KB_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows, {row["id"]: row for row in rows if row["id"] in TARGET_IDS}


def test_nrc_replacement_rows_exclude_old_application_evidence():
    _, target_rows = load_target_rows()

    assert set(target_rows) == TARGET_IDS
    combined = "\n".join(value for row in target_rows.values() for value in row.values())
    assert OLD_NRC_URL not in combined
    assert "0.6-0.7 nCi" not in combined
    assert "0.6–0.7 nCi" not in combined
    assert "120 nCi" not in combined


def test_i125_replacement_omits_precise_parameters_not_supported_by_new_sources():
    _, target_rows = load_target_rows()
    row = target_rows["KB-RECO-0090"]
    source_scoped_text = "\n".join((row["hazard_types"], row["answer"]))

    assert "27-35 keV" not in source_scoped_text
    assert "60.1天" not in source_scoped_text
    assert "半衰期约60天" not in source_scoped_text


def test_sewer_disposal_replacement_names_appendix_b_table_3():
    _, target_rows = load_target_rows()
    row = target_rows["KB-RECO-0099"]
    evidence_text = "\n".join((row["answer"], row["references"], row["source_version"]))

    assert "Table 3" in evidence_text
    assert "审批信息" not in row["answer"]


def test_current_unique_source_title_count_is_1276():
    rows, _ = load_target_rows()

    assert len({row["source_title"] for row in rows}) == 1276
