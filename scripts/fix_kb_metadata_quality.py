#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEGAL_CITATION_RE = re.compile(
    r"\b(?:\d+\s*CFR|CFR|RCRA|TSCA|OSHA|NFPA|ANSI|IAEA|NRC|CDC/NIH|BMBL|GB(?:/T)?\s*\d+|HJ\s*\d+|AQ\s*\d+)\b",
    re.IGNORECASE,
)


def compact(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def is_valid_risk_level(value: str) -> bool:
    if not value:
        return False
    try:
        risk = int(float(value))
    except ValueError:
        return False
    return 1 <= risk <= 5


def has_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)


def append_unique(existing: str, addition: str) -> str:
    existing = compact(existing)
    addition = compact(addition)
    if not addition:
        return existing
    if not existing:
        return addition
    parts = [compact(p) for p in re.split(r"[;；]", existing) if compact(p)]
    if addition in parts or addition in existing:
        return existing
    return f"{existing}; {addition}"


def infer_subcategory(row: dict[str, str]) -> str:
    text = " ".join(
        compact(row.get(key))
        for key in (
            "id",
            "title",
            "category",
            "hazard_types",
            "scenario",
            "question",
            "answer",
            "steps",
            "ppe",
            "forbidden",
            "disposal",
            "first_aid",
            "emergency",
            "source_title",
            "tags",
        )
    )
    category = compact(row.get("category"))

    if has_any(text, ("废液", "废物", "危废", "waste", "disposal", "dispose", "RCRA", "Universal Waste")):
        return "危废处置"
    if has_any(text, ("氢氟酸", "HF", "泄漏", "暴露", "急救", "中毒", "洗眼", "淋浴", "应急", "spill", "exposure")):
        return "化学应急" if category == "化学" else "应急"
    if has_any(text, ("PPE", "个体防护", "个人防护", "手套", "护目", "面罩", "呼吸防护", "lab coat")):
        return "PPE"
    if has_any(text, ("气瓶", "压缩气体", "无水氨", "氯气", "compressed gas", "gas cylinder")):
        return "气体安全"
    if has_any(text, ("液氮", "低温", "深冷", "cryogen", "cryogenic")):
        return "低温安全"
    if has_any(text, ("易燃", "爆炸", "过氧化", "氧化", "自燃", "水反应", "反应性", "flammable", "reactive")):
        return "反应性/易燃易爆"
    if has_any(text, ("储存", "贮存", "兼容", "相容", "隔离", "storage", "segregation", "cabinet")):
        return "危化品储存" if category == "化学" else "储存管理"
    if has_any(text, ("SDS", "MSDS", "HCS", "标签", "标识", "危害沟通", "hazard communication")):
        return "危害沟通"
    if has_any(text, ("暴露限值", "职业暴露", "PEL", "IDLH", "OEL", "NIOSH Pocket Guide")):
        return "职业暴露"
    if has_any(text, ("生物安全柜", "biosafety cabinet", "BSC")):
        return "生物安全柜"
    if has_any(text, ("高压灭菌", "灭菌", "autoclave")):
        return "灭菌与高压灭菌"
    if has_any(text, ("离心机", "centrifuge")):
        return "离心设备"
    if has_any(text, ("通风柜", "fume hood", "排风")):
        return "通风柜"
    if has_any(text, ("电气", "用电", "触电", "electrical")):
        return "电气设备"
    if has_any(text, ("激光", "laser")):
        return "激光安全"
    if has_any(text, ("辐射", "放射", "radioactive", "radiation", "NRC")):
        return "辐射安全"
    if has_any(text, ("培训", "training")):
        return "培训"
    if has_any(text, ("制度", "规范", "标准", "管理要求", "standard", "regulation")):
        return "安全制度"

    defaults = {
        "化学": "危化品安全",
        "设备": "通用设备",
        "通用": "通用安全",
        "废弃物": "危废处置",
        "物理": "物理危害",
        "标准": "安全制度",
        "生物": "生物安全",
        "电气": "电气设备",
        "消防": "消防安全",
        "应急": "应急",
        "辐射": "辐射安全",
        "PPE": "PPE",
        "培训": "培训",
    }
    return defaults.get(category, category or "通用安全")


def infer_risk_level(row: dict[str, str], subcategory: str) -> str:
    text = " ".join(
        compact(row.get(key))
        for key in (
            "title",
            "category",
            "hazard_types",
            "scenario",
            "question",
            "answer",
            "forbidden",
            "disposal",
            "first_aid",
            "emergency",
            "source_title",
            "tags",
            "legal_notes",
        )
    )
    category = compact(row.get("category"))
    subcategory = compact(subcategory)

    if has_any(
        text,
        (
            "氢氟酸",
            "HF",
            "氰化",
            "剧毒",
            "爆炸",
            "火灾",
            "触电",
            "中毒",
            "放射",
            "辐射",
            "选择制剂",
            "水反应",
            "自燃",
            "pyrophoric",
            "water-reactive",
            "IDLH",
        ),
    ):
        return "5"
    if has_any(
        text,
        (
            "危险废物",
            "危废",
            "RCRA",
            "腐蚀",
            "强氧化",
            "易燃",
            "过氧化",
            "压缩气体",
            "液氮",
            "高压灭菌",
            "生物安全",
            "血源性",
            "致癌",
            "formaldehyde",
            "methylene chloride",
            "dichloromethane",
            "beryllium",
            "cadmium",
            "lead",
            "mercury",
        ),
    ):
        return "4"
    if category in {"废弃物", "生物", "辐射"} or subcategory in {"危废处置", "辐射安全", "激光安全"}:
        return "4"
    if category in {"化学", "设备", "电气", "消防", "应急", "物理"}:
        return "3"
    if category in {"通用", "PPE", "培训", "标准"}:
        return "2"
    return "2"


def build_reference(row: dict[str, str]) -> str:
    source_title = compact(row.get("source_title"))
    source_org = compact(row.get("source_org"))
    source_url = compact(row.get("source_url"))
    pieces = []
    if source_title:
        pieces.append(source_title)
    if source_org:
        pieces.append(source_org)
    if source_url:
        pieces.append(source_url)
    return "; ".join(pieces)


def normalize_references(row: dict[str, str]) -> tuple[str, list[str]]:
    references = compact(row.get("references"))
    source_title = compact(row.get("source_title"))
    source_org = compact(row.get("source_org"))
    source_url = compact(row.get("source_url"))
    source_reference = build_reference(row)
    changes: list[str] = []
    missing_source_title = bool(source_title and source_title not in references)
    missing_source_org = bool(source_org and source_org not in references)

    if "待补充" in references:
        references = "; ".join(part for part in re.split(r"[;；]", references) if compact(part) and "待补充" not in part)
        changes.append("references_placeholder_replaced")

    if not references:
        references = source_reference
        if references:
            changes.append("references_filled")
    elif source_url and source_url not in references:
        references = append_unique(references, source_reference or source_url)
        changes.append("references_source_url_appended")

    if source_url and source_url not in references:
        references = append_unique(references, source_url)
        if "references_source_url_appended" not in changes:
            changes.append("references_source_url_appended")

    if missing_source_title and source_title not in references:
        references = append_unique(references, source_reference or source_title)
        changes.append("references_source_title_appended")

    if missing_source_org and source_org not in references:
        references = append_unique(references, source_reference or source_org)
        changes.append("references_source_org_appended")
    elif missing_source_org and source_org in references:
        changes.append("references_source_org_appended")

    return references, changes


def normalize_row(row: dict[str, str], updated_at: str | None = None) -> tuple[dict[str, str], list[str]]:
    updated = dict(row)
    changes: list[str] = []
    risk = compact(updated.get("risk_level"))

    if risk and not is_valid_risk_level(risk):
        if LEGAL_CITATION_RE.search(risk):
            updated["legal_notes"] = append_unique(updated.get("legal_notes", ""), risk)
            changes.append("risk_level_legal_citation_moved")
        else:
            updated["legal_notes"] = append_unique(updated.get("legal_notes", ""), f"原risk_level非数字值：{risk}")
            changes.append("risk_level_invalid_value_moved")
        updated["risk_level"] = ""
        risk = ""

    subcategory = compact(updated.get("subcategory"))
    if not subcategory:
        subcategory = infer_subcategory(updated)
        updated["subcategory"] = subcategory
        changes.append("subcategory_inferred")

    if not risk:
        updated["risk_level"] = infer_risk_level(updated, subcategory)
        changes.append("risk_level_inferred")

    references, reference_changes = normalize_references(updated)
    if reference_changes:
        updated["references"] = references
        changes.extend(reference_changes)

    if changes and "last_updated" in updated and updated_at:
        updated["last_updated"] = updated_at

    return updated, changes


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fix deterministic metadata quality issues in knowledge_base_curated.csv")
    parser.add_argument("--kb", default=str(REPO_ROOT / "knowledge_base_curated.csv"))
    parser.add_argument("--report-dir", default=str(REPO_ROOT / "artifacts/kb_traceability_20260718"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--updated-at", default=date.today().isoformat())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kb_path = Path(args.kb).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    headers, rows = read_csv(kb_path)

    updated_rows: list[dict[str, str]] = []
    change_rows: list[dict[str, str]] = []
    change_counts: Counter[str] = Counter()
    for row in rows:
        updated, changes = normalize_row(row, updated_at=args.updated_at)
        updated_rows.append(updated)
        for change in changes:
            change_counts[change] += 1
        if changes:
            change_rows.append(
                {
                    "id": compact(row.get("id")),
                    "title": compact(row.get("title")),
                    "category": compact(row.get("category")),
                    "old_subcategory": compact(row.get("subcategory")),
                    "new_subcategory": compact(updated.get("subcategory")),
                    "old_risk_level": compact(row.get("risk_level")),
                    "new_risk_level": compact(updated.get("risk_level")),
                    "source_url": compact(row.get("source_url")),
                    "changes": ";".join(changes),
                }
            )

    report_csv = report_dir / ("kb_metadata_fix_dry_run.csv" if args.dry_run else "kb_metadata_fix_applied.csv")
    with report_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "title",
                "category",
                "old_subcategory",
                "new_subcategory",
                "old_risk_level",
                "new_risk_level",
                "source_url",
                "changes",
            ],
        )
        writer.writeheader()
        writer.writerows(change_rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kb_path": str(kb_path),
        "dry_run": args.dry_run,
        "row_count": len(rows),
        "changed_row_count": len(change_rows),
        "change_counts": dict(change_counts.most_common()),
        "report_csv": str(report_csv),
    }
    summary_path = report_dir / ("kb_metadata_fix_dry_run_summary.json" if args.dry_run else "kb_metadata_fix_applied_summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.dry_run:
        backup_path = report_dir / "knowledge_base_curated.before_metadata_fix.csv"
        if not backup_path.exists():
            shutil.copy2(kb_path, backup_path)
        write_csv(kb_path, headers, updated_rows)

    print(f"[done] dry_run={args.dry_run} changed_rows={len(change_rows)}")
    print(f"[done] change_counts={dict(change_counts.most_common())}")
    print(f"[done] report={report_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
