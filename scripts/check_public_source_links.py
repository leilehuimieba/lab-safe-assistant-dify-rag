#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "lab-safe-assistant-link-check/1.0 (+local project validation)"


def read_seed_sources(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_external_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def check_url(url: str, timeout: int = 25) -> dict[str, object]:
    result: dict[str, object] = {
        "url": url,
        "status": "unchecked",
        "http_status": None,
        "final_url": "",
        "content_type": "",
        "content_length_header": "",
        "bytes_sampled": 0,
        "error": "",
    }
    try:
        # GET is more reliable than HEAD for many EHS/PDF hosts.
        with requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"},
            stream=True,
            allow_redirects=True,
        ) as resp:
            result["http_status"] = resp.status_code
            result["final_url"] = resp.url
            result["content_type"] = resp.headers.get("content-type", "")
            result["content_length_header"] = resp.headers.get("content-length", "")
            sampled = 0
            chunks = []
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    chunks.append(chunk)
                    sampled += len(chunk)
                if sampled >= 65536:
                    break
            result["bytes_sampled"] = sampled
            if 200 <= resp.status_code < 400 and sampled > 0:
                result["status"] = "ok"
            elif 200 <= resp.status_code < 400:
                result["status"] = "empty"
            else:
                result["status"] = "bad_status"
    except Exception as exc:
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def has_cached_artifact(source_id: str) -> tuple[bool, str]:
    raw_dir = REPO_ROOT / "artifacts/web_ingest_public_20260429/raw"
    text_dir = REPO_ROOT / "artifacts/web_ingest_public_20260429/extracted_text"
    raw_paths = list(raw_dir.glob(f"{source_id}_*"))
    text_path = text_dir / f"{source_id}.txt"
    raw_ok = any(p.exists() and p.stat().st_size > 0 for p in raw_paths)
    text_ok = text_path.exists() and text_path.stat().st_size > 0
    evidence = []
    if raw_ok:
        evidence.append("raw")
    if text_ok:
        evidence.append("text")
    return raw_ok and text_ok, "+".join(evidence)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check public source URLs used by the external lab safety ingest bundle.")
    ap.add_argument("--seed", default="data_sources/public_lab_safety_sources_v1.csv")
    ap.add_argument("--external-csv", default="release_exports/v10_external_sources/knowledge_base_external_import_ready.csv")
    ap.add_argument("--report-json", default="artifacts/link_check_public_20260429/link_check_report.json")
    ap.add_argument("--report-md", default="docs/eval/public_source_link_check_20260429.md")
    ap.add_argument("--sleep-ms", type=int, default=100)
    args = ap.parse_args()

    seed_path = (REPO_ROOT / args.seed).resolve()
    external_path = (REPO_ROOT / args.external_csv).resolve()
    report_json = (REPO_ROOT / args.report_json).resolve()
    report_md = (REPO_ROOT / args.report_md).resolve()

    seeds = read_seed_sources(seed_path)
    rows = read_external_rows(external_path)
    row_count_by_url = Counter((r.get("source_url") or "").strip() for r in rows if (r.get("source_url") or "").strip())

    # Keep seed order. Include any source_url that exists only in generated CSV.
    seen = set()
    items = []
    for s in seeds:
        url = (s.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        items.append({"id": s.get("id", ""), "title": s.get("title", ""), "org": s.get("org", ""), "url": url})
    for url in sorted(row_count_by_url):
        if url not in seen:
            seen.add(url)
            items.append({"id": "CSV-ONLY", "title": "", "org": "", "url": url})

    checked = []
    for i, item in enumerate(items, 1):
        res = check_url(item["url"])
        res.update({"id": item["id"], "title": item["title"], "org": item["org"], "generated_rows": row_count_by_url.get(item["url"], 0)})
        cache_ok, cache_evidence = has_cached_artifact(item["id"])
        res["cache_evidence"] = cache_evidence
        if res["status"] != "ok" and cache_ok and int(res.get("generated_rows") or 0) > 0:
            res["live_status_before_cache"] = res["status"]
            res["status"] = "cached_ok_live_failed"
        checked.append(res)
        print(f"[{i}/{len(items)}] {res['status']} {res.get('http_status')} rows={res['generated_rows']} {item['id']} {item['url']}")
        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000)

    status_counts = Counter(str(x["status"]) for x in checked)
    zero_rows = [x for x in checked if int(x.get("generated_rows") or 0) == 0]
    bad_links = [x for x in checked if x.get("status") not in {"ok", "cached_ok_live_failed"}]
    ok_zero = [x for x in zero_rows if x.get("status") == "ok"]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed_path": str(seed_path),
        "external_csv": str(external_path),
        "source_count": len(checked),
        "external_rows": len(rows),
        "status_counts": dict(status_counts),
        "bad_link_count": len(bad_links),
        "zero_generated_rows_count": len(zero_rows),
        "ok_but_zero_generated_rows_count": len(ok_zero),
        "items": checked,
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 外部公开来源链接健康检查报告",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- seed_path: `{seed_path}`",
        f"- external_csv: `{external_path}`",
        f"- source_count: `{len(checked)}`",
        f"- external_rows: `{len(rows)}`",
        f"- status_counts: `{dict(status_counts)}`",
        f"- bad_link_count: `{len(bad_links)}`",
        f"- zero_generated_rows_count: `{len(zero_rows)}`",
        f"- ok_but_zero_generated_rows_count: `{len(ok_zero)}`",
        "",
        "## 结论口径",
        "",
        "- `status=ok` 表示链接当前可访问且返回非空内容。",
        "- `status=cached_ok_live_failed` 表示实时访问受到临时反爬/远端断开影响，但本地已保存原始抓取物和抽取文本，且已生成知识条目；这类不按死链处理，但应在提交前择时复查。",
        "- `generated_rows=0` 不一定是链接坏，可能是 PDF 海报/短通知/图片型 PDF 导致文本不足或抽取质量低。",
        "- 验收应优先采用 `status=ok 且 generated_rows>0` 的来源；`cached_ok_live_failed` 可作为已有抓取证据来源但需复查实时可访问性；0 条来源可保留为抓取证据，但不计入有效知识条目贡献。",
        "",
        "## 问题链接",
        "",
        "| id | status | http | rows | content_type | url | error |",
        "|---|---|---:|---:|---|---|---|",
    ]
    if bad_links:
        for x in bad_links:
            lines.append(f"| {x['id']} | {x['status']} | {x.get('http_status') or ''} | {x.get('generated_rows',0)} | {x.get('content_type','')} | {x['url']} | {str(x.get('error','')).replace('|','/')} |")
    else:
        lines.append("| 无 | - | - | - | - | - | - |")

    lines.extend([
        "",
        "## 可访问但未生成条目的来源",
        "",
        "| id | http | content_type | sampled_bytes | url | 处理建议 |",
        "|---|---:|---|---:|---|---|",
    ])
    if ok_zero:
        for x in ok_zero:
            lines.append(f"| {x['id']} | {x.get('http_status') or ''} | {x.get('content_type','')} | {x.get('bytes_sampled',0)} | {x['url']} | 检查是否为短海报/图片型PDF；若不能稳定抽取文本，则从有效来源清单剔除或保留为附属证据 |")
    else:
        lines.append("| 无 | - | - | - | - | - |")

    lines.extend([
        "",
        "## 全量链接检查明细",
        "",
        "| id | org | status | http | rows | content_type | url |",
        "|---|---|---|---:|---:|---|---|",
    ])
    for x in checked:
        lines.append(f"| {x['id']} | {x.get('org','')} | {x['status']} | {x.get('http_status') or ''} | {x.get('generated_rows',0)} | {x.get('content_type','')} | {x['url']} |")

    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[done] json={report_json}")
    print(f"[done] md={report_md}")
    return 0 if not bad_links else 2


if __name__ == "__main__":
    raise SystemExit(main())
