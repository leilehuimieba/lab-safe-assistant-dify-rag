#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def classify_pdf(generated_rows: int, text_chars: int, raw_bytes: int) -> tuple[str, str]:
    if generated_rows > 0 and text_chars >= 2000:
        return "text_ingested", "PDF 已成功抽取正文并生成结构化知识条目，可计入有效知识库。"
    if generated_rows > 0:
        return "short_text_ingested", "PDF 文本较短但已生成少量条目，可计入有效条目但建议人工复核。"
    if text_chars < 800 and raw_bytes > 50000:
        return "image_or_poster_pdf", "PDF 可访问但文本很少，疑似海报/图片型 PDF；建议 OCR 或人工摘要，不计入有效条目贡献。"
    if text_chars < 2000:
        return "short_notice_pdf", "PDF 可访问但正文不足，适合作为附属证据或人工摘要，不自动计入有效条目。"
    return "needs_review", "PDF 已抽取文本但未形成条目，需检查分段规则或人工摘要。"


def main() -> int:
    link_path = REPO_ROOT / "artifacts/link_check_public_20260429/link_check_report.json"
    text_dir = REPO_ROOT / "artifacts/web_ingest_public_20260429/extracted_text"
    raw_dir = REPO_ROOT / "artifacts/web_ingest_public_20260429/raw"
    out_json = REPO_ROOT / "artifacts/pdf_audit_public_20260429/pdf_audit_report.json"
    out_md = REPO_ROOT / "docs/eval/public_pdf_processing_report_20260429.md"

    link = json.loads(link_path.read_text(encoding="utf-8"))
    items = []
    for x in link["items"]:
        ctype = (x.get("content_type") or "").lower()
        url = x.get("url") or ""
        if "pdf" not in ctype and not url.lower().endswith(".pdf"):
            continue
        sid = x["id"]
        text_path = text_dir / f"{sid}.txt"
        raw_paths = list(raw_dir.glob(f"{sid}_*"))
        text_chars = len(text_path.read_text(encoding="utf-8", errors="ignore")) if text_path.exists() else 0
        raw_bytes = sum(p.stat().st_size for p in raw_paths)
        generated_rows = int(x.get("generated_rows") or 0)
        bucket, action = classify_pdf(generated_rows, text_chars, raw_bytes)
        items.append({
            "id": sid,
            "org": x.get("org", ""),
            "url": url,
            "http_status": x.get("http_status"),
            "content_type": x.get("content_type", ""),
            "generated_rows": generated_rows,
            "text_chars": text_chars,
            "raw_bytes": raw_bytes,
            "bucket": bucket,
            "recommended_action": action,
            "text_path": str(text_path) if text_path.exists() else "",
            "raw_paths": [str(p) for p in raw_paths],
        })

    counts = Counter(i["bucket"] for i in items)
    effective_rows = sum(i["generated_rows"] for i in items)
    zero_items = [i for i in items if i["generated_rows"] == 0]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pdf_source_count": len(items),
        "pdf_generated_rows": effective_rows,
        "bucket_counts": dict(counts),
        "zero_pdf_count": len(zero_items),
        "items": items,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 外部 PDF 来源处理报告",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- pdf_source_count: `{payload['pdf_source_count']}`",
        f"- pdf_generated_rows: `{payload['pdf_generated_rows']}`",
        f"- bucket_counts: `{payload['bucket_counts']}`",
        f"- zero_pdf_count: `{payload['zero_pdf_count']}`",
        "",
        "## 处理原则",
        "",
        "1. 正文型 PDF：用 `pdfminer.six` 自动抽取文本，按章节/语义段生成知识条目，并保留原始 PDF 与抽取文本。",
        "2. 短通知/海报型 PDF：链接和原件保留为证据，但如果抽取文本不足，不硬凑为知识条目。",
        "3. 图片/扫描型 PDF：后续可走 OCR 或人工摘要；OCR/人工处理前，不计入有效知识条目贡献。",
        "4. 所有 PDF 条目都保留 `source_url/source_title/source_org`，便于 Dify 引用追溯和人工审核。",
        "",
        "## 分类统计",
        "",
        "| 分类 | 数量 | 含义 |",
        "|---|---:|---|",
        f"| text_ingested | {counts.get('text_ingested', 0)} | 已抽取正文并生成条目 |",
        f"| short_text_ingested | {counts.get('short_text_ingested', 0)} | 文本较短但已生成少量条目 |",
        f"| image_or_poster_pdf | {counts.get('image_or_poster_pdf', 0)} | 疑似海报/图片型 PDF，需 OCR 或人工摘要 |",
        f"| short_notice_pdf | {counts.get('short_notice_pdf', 0)} | 短通知 PDF，不自动计入有效条目 |",
        f"| needs_review | {counts.get('needs_review', 0)} | 已抽取文本但分段未形成条目，需复核 |",
        "",
        "## 需要 OCR / 人工摘要的 PDF",
        "",
        "| id | text_chars | raw_bytes | url | 建议 |",
        "|---|---:|---:|---|---|",
    ]
    need_manual = [i for i in items if i["generated_rows"] == 0]
    if need_manual:
        for i in need_manual:
            lines.append(f"| {i['id']} | {i['text_chars']} | {i['raw_bytes']} | {i['url']} | {i['recommended_action']} |")
    else:
        lines.append("| 无 | - | - | - | - |")

    lines.extend([
        "",
        "## 全量 PDF 明细",
        "",
        "| id | bucket | rows | text_chars | raw_bytes | url |",
        "|---|---|---:|---:|---:|---|",
    ])
    for i in sorted(items, key=lambda x: (x["bucket"], x["id"])):
        lines.append(f"| {i['id']} | {i['bucket']} | {i['generated_rows']} | {i['text_chars']} | {i['raw_bytes']} | {i['url']} |")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[done] {out_md}")
    print(f"[done] {out_json}")
    print(json.dumps({k: payload[k] for k in ['pdf_source_count','pdf_generated_rows','bucket_counts','zero_pdf_count']}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
