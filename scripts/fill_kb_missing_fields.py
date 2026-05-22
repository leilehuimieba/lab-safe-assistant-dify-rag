#!/usr/bin/env python3
"""补齐知识库缺失字段：

1. 若 answer 为空，则用 question 的正文回填；
2. 若 source_title 为空，则根据 source_url / source_org / title 生成。
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill missing fields in knowledge_base_curated.csv")
    parser.add_argument(
        "--kb",
        default=str(REPO_ROOT / "knowledge_base_curated.csv"),
        help="Path to knowledge_base_curated.csv",
    )
    return parser.parse_args()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def title_base(title: str) -> str:
    base = compact_text(title)
    for suffix in ["实验室安全使用", "安全操作规范", "安全操作", "安全使用", "特殊安全要求"]:
        if base.endswith(suffix):
            base = base[: -len(suffix)].rstrip("（(").rstrip()
    return base or compact_text(title)


def fill_answer(row: dict[str, str]) -> str:
    answer = compact_text(row.get("answer", ""))
    if answer:
        return answer
    question = compact_text(row.get("question", ""))
    if not question:
        return compact_text(row.get("title", ""))
    return question


def resolve_source_title(row: dict[str, str]) -> str:
    current = compact_text(row.get("source_title", ""))
    if current:
        return current

    source_url = compact_text(row.get("source_url", ""))
    source_org = compact_text(row.get("source_org", ""))
    base = title_base(row.get("title", ""))

    explicit_map = {
        "https://ehs.stanford.edu/reference/autoclave-safety": "Stanford Autoclave Safety",
        "https://ehs.stanford.edu/reference/centrifuge-safety": "Stanford Centrifuge Safety",
        "https://ehs.stanford.edu/manual/laboratory-standard-design-guidelines/biological-safety-cabinets-and-other-containment": "Stanford Biological Safety Cabinets and Other Containment",
        "https://ehs.stanford.edu/manual/biosafety-manual/autoclaves": "Stanford Biosafety Manual - Autoclaves",
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards": "Cornell Laboratory Safety Manual Ch.16 Physical Hazards",
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1610": "Cornell Laboratory Safety Manual Ch.16.10 Cryogenic Materials",
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1612-glass-under-vacuum": "Cornell Laboratory Safety Manual Ch.16.12 Glass Under Vacuum",
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/164-compressed-gases": "Cornell Laboratory Safety Manual Ch.16.4 Compressed Gases",
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and-heating-devices": "Cornell Laboratory Safety Manual Ch.16.6 Heat and Heating Devices",
        "https://ehs.cornell.edu/shipping-and-transportation/hazardous-materials-shipping-dot/cryogen-tips": "Cornell Cryogen Tips",
        "https://www.ncbi.nlm.nih.gov/books/NBK55872/": "Prudent Practices in the Laboratory (NCBI Bookshelf)",
        "https://www.agilent.com/en/product/liquid-chromatography/mass-spectrometry-lc-ms": "Agilent LC/MS Safety Resources",
        "https://www.osha.gov/SLTC/sulfuricacid/": "OSHA Sulfuric Acid",
        "https://www.osha.gov/formaldehyde": "OSHA Formaldehyde",
        "https://www.epa.gov/mercury/what-do-if-you-spill-more-mercury-amount-thermometer": "EPA Mercury Spills",
    }
    if source_url in explicit_map:
        return explicit_map[source_url]

    if "cdc.gov/niosh/npg/" in source_url:
        return f"NIOSH Pocket Guide to Chemical Hazards - {base}"
    if "cdc.gov/niosh/idlh/" in source_url:
        return f"NIOSH IDLH - {base}"
    if "osha.gov/chemicaldata/" in source_url:
        return f"OSHA Chemical Sampling Information - {base}"

    if "Cornell" in source_org:
        return f"{source_org} Reference - {base}"
    if "Stanford" in source_org:
        return f"{source_org} Reference - {base}"
    if "OSHA" in source_org:
        return f"{source_org} Reference - {base}"
    if "NIOSH" in source_org or "Centers for Disease Control and Prevention" in source_org:
        return f"{source_org} Reference - {base}"
    if "Agilent" in source_org:
        return f"{source_org} Reference - {base}"
    if "EPA" in source_org:
        return f"{source_org} Reference - {base}"
    if "National Academies" in source_org:
        return f"{source_org} Reference - {base}"

    return base or "Source Reference"


def main() -> int:
    args = parse_args()
    kb_path = Path(args.kb).resolve()
    headers, rows = read_csv(kb_path)
    if not rows:
        raise SystemExit(f"No rows found in {kb_path}")

    before_missing_answer = sum(1 for r in rows if not compact_text(r.get("answer", "")))
    before_missing_source = sum(1 for r in rows if not compact_text(r.get("source_title", "")))

    answer_filled = 0
    source_filled = 0
    source_counter: Counter[str] = Counter()

    updated_rows: list[dict[str, str]] = []
    for row in rows:
        current = dict(row)
        if not compact_text(current.get("answer", "")):
            current["answer"] = fill_answer(current)
            if compact_text(current["answer"]):
                answer_filled += 1
        if not compact_text(current.get("source_title", "")):
            current["source_title"] = resolve_source_title(current)
            if compact_text(current["source_title"]):
                source_filled += 1
                source_counter[current["source_title"]] += 1
        updated_rows.append(current)

    write_csv(kb_path, headers, updated_rows)

    after_missing_answer = sum(1 for r in updated_rows if not compact_text(r.get("answer", "")))
    after_missing_source = sum(1 for r in updated_rows if not compact_text(r.get("source_title", "")))

    print(f"[OK] updated kb: {kb_path}")
    print(f"[OK] answer filled: {answer_filled} | before={before_missing_answer} after={after_missing_answer}")
    print(f"[OK] source_title filled: {source_filled} | before={before_missing_source} after={after_missing_source}")
    print("[INFO] top generated source_title values:")
    for title, count in source_counter.most_common(12):
        print(f"  - {count} x {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
