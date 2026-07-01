from __future__ import annotations

"""知识库 CSV schema 单一来源。

- KB_HEADERS: knowledge_base_curated.csv 完整 29 列（权威顺序）。
- DIFY_IMPORT_FIELDS: 导入 Dify Dataset 时要写入的字段子集。
  刻意排除 id/last_updated/reviewer/status（这四列是内部治理字段，
  不属于 Dify 里的"知识内容"），排除结果由 KB_INTERNAL_FIELDS 表达。

修改 knowledge_base_curated.csv 表头时，必须同步更新本文件；
scripts/quality_gate.py 会校验实际表头与 KB_HEADERS 一致。
"""

KB_HEADERS: tuple[str, ...] = (
    "id",
    "title",
    "category",
    "subcategory",
    "lab_type",
    "risk_level",
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
    "legal_notes",
    "references",
    "source_type",
    "source_title",
    "source_org",
    "source_version",
    "source_date",
    "source_url",
    "last_updated",
    "reviewer",
    "status",
    "tags",
    "language",
)

KB_INTERNAL_FIELDS: frozenset[str] = frozenset({"id", "last_updated", "reviewer", "status"})

DIFY_IMPORT_FIELDS: tuple[str, ...] = tuple(
    h for h in KB_HEADERS if h not in KB_INTERNAL_FIELDS
)
