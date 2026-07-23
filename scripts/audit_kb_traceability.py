#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "lab-safe-assistant-kb-traceability-audit/1.0 (+local project validation)"
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
REQUIRED_SOURCE_FIELDS = ("source_title", "source_org", "source_url")


def compact(text: object) -> str:
    return str(text or "").strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_valid_risk_level(value: str) -> bool:
    if not value:
        return False
    try:
        risk = int(float(value))
    except ValueError:
        return False
    return 1 <= risk <= 5


def audit_rows(rows: list[dict[str, str]]) -> dict[str, object]:
    missing_source_fields = Counter()
    invalid_url_rows: list[dict[str, str]] = []
    invalid_risk_rows: list[dict[str, str]] = []
    missing_risk_rows: list[dict[str, str]] = []
    missing_subcategory_rows: list[dict[str, str]] = []
    missing_references_rows: list[dict[str, str]] = []
    references_placeholder_rows: list[dict[str, str]] = []
    references_without_source_title_rows: list[dict[str, str]] = []
    references_without_source_org_rows: list[dict[str, str]] = []
    references_without_source_url_rows: list[dict[str, str]] = []
    rows_by_source_url: Counter[str] = Counter()
    rows_by_domain: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    source_org_counts: Counter[str] = Counter()

    for row in rows:
        url = compact(row.get("source_url"))
        risk = compact(row.get("risk_level"))

        for field in REQUIRED_SOURCE_FIELDS:
            if not compact(row.get(field)):
                missing_source_fields[field] += 1

        if url:
            rows_by_source_url[url] += 1
            if not is_valid_url(url):
                invalid_url_rows.append(row)
            else:
                rows_by_domain[urlparse(url).netloc.lower()] += 1

        if not risk:
            missing_risk_rows.append(row)
        elif not is_valid_risk_level(risk):
            invalid_risk_rows.append(row)

        if not compact(row.get("subcategory")):
            missing_subcategory_rows.append(row)
        references = compact(row.get("references"))
        if not references:
            missing_references_rows.append(row)
        else:
            if "待补充" in references:
                references_placeholder_rows.append(row)
            source_title = compact(row.get("source_title"))
            source_org = compact(row.get("source_org"))
            if source_title and source_title not in references:
                references_without_source_title_rows.append(row)
            if source_org and source_org not in references:
                references_without_source_org_rows.append(row)
            if url and is_valid_url(url) and url not in references:
                references_without_source_url_rows.append(row)
        status_counts[compact(row.get("status")) or "(blank)"] += 1
        source_org_counts[compact(row.get("source_org")) or "(blank)"] += 1

    return {
        "row_count": len(rows),
        "missing_source_title_count": missing_source_fields["source_title"],
        "missing_source_org_count": missing_source_fields["source_org"],
        "missing_source_url_count": missing_source_fields["source_url"],
        "invalid_source_url_count": len(invalid_url_rows),
        "missing_risk_level_count": len(missing_risk_rows),
        "invalid_risk_level_count": len(invalid_risk_rows),
        "missing_subcategory_count": len(missing_subcategory_rows),
        "missing_references_count": len(missing_references_rows),
        "references_placeholder_count": len(references_placeholder_rows),
        "references_without_source_title_count": len(references_without_source_title_rows),
        "references_without_source_org_count": len(references_without_source_org_rows),
        "references_without_source_url_count": len(references_without_source_url_rows),
        "unique_source_url_count": len(rows_by_source_url),
        "rows_by_source_url": dict(rows_by_source_url),
        "rows_by_domain": dict(rows_by_domain.most_common()),
        "status_counts": dict(status_counts.most_common()),
        "source_org_counts": dict(source_org_counts.most_common()),
        "problem_rows": build_problem_rows(
            rows,
            invalid_url_rows,
            invalid_risk_rows,
            missing_risk_rows,
            missing_subcategory_rows,
            missing_references_rows,
            references_placeholder_rows,
            references_without_source_title_rows,
            references_without_source_org_rows,
            references_without_source_url_rows,
        ),
    }


def build_problem_rows(
    rows: list[dict[str, str]],
    invalid_url_rows: list[dict[str, str]],
    invalid_risk_rows: list[dict[str, str]],
    missing_risk_rows: list[dict[str, str]],
    missing_subcategory_rows: list[dict[str, str]],
    missing_references_rows: list[dict[str, str]],
    references_placeholder_rows: list[dict[str, str]],
    references_without_source_title_rows: list[dict[str, str]],
    references_without_source_org_rows: list[dict[str, str]],
    references_without_source_url_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    invalid_url_ids = {id(r) for r in invalid_url_rows}
    invalid_risk_ids = {id(r) for r in invalid_risk_rows}
    missing_risk_ids = {id(r) for r in missing_risk_rows}
    missing_subcategory_ids = {id(r) for r in missing_subcategory_rows}
    missing_references_ids = {id(r) for r in missing_references_rows}
    references_placeholder_ids = {id(r) for r in references_placeholder_rows}
    references_without_source_title_ids = {id(r) for r in references_without_source_title_rows}
    references_without_source_org_ids = {id(r) for r in references_without_source_org_rows}
    references_without_source_url_ids = {id(r) for r in references_without_source_url_rows}
    problem_rows: list[dict[str, object]] = []

    for row in rows:
        issues = []
        if not compact(row.get("source_title")):
            issues.append("missing_source_title")
        if not compact(row.get("source_org")):
            issues.append("missing_source_org")
        if not compact(row.get("source_url")):
            issues.append("missing_source_url")
        if id(row) in invalid_url_ids:
            issues.append("invalid_source_url")
        if id(row) in missing_risk_ids:
            issues.append("missing_risk_level")
        if id(row) in invalid_risk_ids:
            issues.append("invalid_risk_level")
        if id(row) in missing_subcategory_ids:
            issues.append("missing_subcategory")
        if id(row) in missing_references_ids:
            issues.append("missing_references")
        if id(row) in references_placeholder_ids:
            issues.append("references_placeholder")
        if id(row) in references_without_source_title_ids:
            issues.append("references_without_source_title")
        if id(row) in references_without_source_org_ids:
            issues.append("references_without_source_org")
        if id(row) in references_without_source_url_ids:
            issues.append("references_without_source_url")
        if not issues:
            continue
        problem_rows.append(
            {
                "id": compact(row.get("id")),
                "title": compact(row.get("title")),
                "category": compact(row.get("category")),
                "subcategory": compact(row.get("subcategory")),
                "risk_level": compact(row.get("risk_level")),
                "source_title": compact(row.get("source_title")),
                "source_org": compact(row.get("source_org")),
                "source_url": compact(row.get("source_url")),
                "issues": ";".join(issues),
            }
        )
    return problem_rows


def check_url(url: str, timeout: int, trust_env: bool = True) -> dict[str, object]:
    result: dict[str, object] = {
        "url": url,
        "status": "unchecked",
        "http_status": None,
        "final_url": "",
        "content_type": "",
        "bytes_sampled": 0,
        "error": "",
    }
    headers_variants = [
        {"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*", "Accept-Encoding": "identity"},
        {
            "User-Agent": BROWSER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
            "Accept-Encoding": "identity",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    ]
    try:
        for attempt, headers in enumerate(headers_variants, 1):
            if trust_env:
                response_context = requests.get(
                    url,
                    timeout=timeout,
                    headers=headers,
                    stream=True,
                    allow_redirects=True,
                )
            else:
                session = requests.Session()
                session.trust_env = False
                response_context = session.get(
                    url,
                    timeout=timeout,
                    headers=headers,
                    stream=True,
                    allow_redirects=True,
                )
            with response_context as resp:
                result["http_status"] = resp.status_code
                result["final_url"] = resp.url
                result["content_type"] = resp.headers.get("content-type", "")
                result["attempt"] = attempt
                sampled = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
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
                if result["status"] == "ok":
                    break
    except Exception as exc:
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def classify_url_result(result: dict[str, object]) -> str:
    status = compact(result.get("status"))
    http_status = result.get("http_status")
    try:
        http_code = int(http_status) if http_status is not None else None
    except (TypeError, ValueError):
        http_code = None

    if status == "ok":
        return "open"
    if status == "empty":
        return "open_empty"
    if http_code in {401, 403, 429}:
        return "blocked_or_forbidden"
    if http_code in {404, 410}:
        return "dead_or_moved"
    if status == "bad_status":
        return "bad_http_status"
    if status == "error":
        return "network_error"
    return status or "unknown"


def load_url_cache(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_url_cache(path: Path, cache: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def audit_urls(
    urls: list[str],
    timeout: int,
    workers: int,
    cache_path: Path,
    sleep_ms: int,
    trust_env: bool = True,
) -> list[dict[str, object]]:
    cache = load_url_cache(cache_path)
    pending = [url for url in urls if url not in cache]
    if pending:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures = {executor.submit(check_url, url, timeout, trust_env): url for url in pending}
            for index, future in enumerate(as_completed(futures), 1):
                url = futures[future]
                cache[url] = future.result()
                cache[url]["checked_at"] = datetime.now(timezone.utc).isoformat()
                print(f"[url {index}/{len(pending)}] {classify_url_result(cache[url])} {url}")
                save_url_cache(cache_path, cache)
                if sleep_ms > 0:
                    time.sleep(sleep_ms / 1000)
    return [cache[url] for url in urls]


def build_url_rows(rows: list[dict[str, str]], url_results: list[dict[str, object]]) -> list[dict[str, object]]:
    by_url: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        url = compact(row.get("source_url"))
        if url:
            by_url[url].append(row)

    out = []
    for result in url_results:
        url = compact(result.get("url"))
        url_rows = by_url.get(url, [])
        orgs = sorted({compact(r.get("source_org")) for r in url_rows if compact(r.get("source_org"))})
        titles = [compact(r.get("source_title")) for r in url_rows if compact(r.get("source_title"))]
        examples = [compact(r.get("id")) for r in url_rows[:5]]
        out.append(
            {
                "url": url,
                "traceability_status": classify_url_result(result),
                "http_status": result.get("http_status") or "",
                "row_count": len(url_rows),
                "source_orgs": ";".join(orgs[:5]),
                "sample_source_title": titles[0] if titles else "",
                "sample_ids": ";".join(examples),
                "final_url": result.get("final_url") or "",
                "content_type": result.get("content_type") or "",
                "bytes_sampled": result.get("bytes_sampled") or 0,
                "error": result.get("error") or "",
            }
        )
    return out


def read_url_rows(path: Path) -> list[dict[str, object]] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def render_markdown(audit: dict[str, object], url_rows: list[dict[str, object]] | None, kb_path: Path) -> str:
    lines = [
        "# 知识库来源追溯与链接审计报告",
        "",
        f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- kb_path: `{kb_path}`",
        f"- row_count: `{audit['row_count']}`",
        f"- unique_source_url_count: `{audit['unique_source_url_count']}`",
        f"- missing_source_title_count: `{audit['missing_source_title_count']}`",
        f"- missing_source_org_count: `{audit['missing_source_org_count']}`",
        f"- missing_source_url_count: `{audit['missing_source_url_count']}`",
        f"- invalid_source_url_count: `{audit['invalid_source_url_count']}`",
        f"- missing_risk_level_count: `{audit['missing_risk_level_count']}`",
        f"- invalid_risk_level_count: `{audit['invalid_risk_level_count']}`",
        f"- missing_subcategory_count: `{audit['missing_subcategory_count']}`",
        f"- missing_references_count: `{audit['missing_references_count']}`",
        f"- references_placeholder_count: `{audit['references_placeholder_count']}`",
        f"- references_without_source_title_count: `{audit['references_without_source_title_count']}`",
        f"- references_without_source_org_count: `{audit['references_without_source_org_count']}`",
        f"- references_without_source_url_count: `{audit['references_without_source_url_count']}`",
        "",
        "## 链接审计口径",
        "",
        "- `open`: 当前网络下可访问，HTTP 2xx/3xx 且返回非空内容。",
        "- `open_empty`: 当前网络下可访问，但抽样内容为空，需要人工确认是否为动态下载或空响应。",
        "- `blocked_or_forbidden`: 链接存在但当前网络被 401/403/429 拒绝，优先寻找可公开访问的等价官方链接。",
        "- `dead_or_moved`: 当前返回 404/410，必须替换为可打开的官方链接，或从知识库移除该来源贡献。",
        "- `network_error`: 连接超时、TLS、远端重置等网络错误，需复查并缓存证据。",
        "",
        "## 字段问题样例",
        "",
        "| id | category | risk_level | issues | source_url |",
        "|---|---|---|---|---|",
    ]
    for row in list(audit["problem_rows"])[:40]:
        lines.append(
            f"| {row['id']} | {row['category']} | {row['risk_level']} | {row['issues']} | {row['source_url']} |"
        )
    if not audit["problem_rows"]:
        lines.append("| 无 | - | - | - | - |")

    lines.extend(["", "## 来源域名 Top 20", "", "| domain | rows |", "|---|---:|"])
    for domain, count in list(dict(audit["rows_by_domain"]).items())[:20]:
        lines.append(f"| {domain} | {count} |")

    if url_rows is not None:
        status_counts = Counter(compact(r.get("traceability_status")) for r in url_rows)
        affected_counts = Counter()
        for row in url_rows:
            affected_counts[compact(row.get("traceability_status"))] += int(row.get("row_count") or 0)
        lines.extend(
            [
                "",
                "## 全量 URL 检查汇总",
                "",
                f"- unique_urls_checked: `{len(url_rows)}`",
                f"- url_status_counts: `{dict(status_counts.most_common())}`",
                f"- affected_row_counts: `{dict(affected_counts.most_common())}`",
                "",
                "## 需整改链接",
                "",
                "| status | http | rows | orgs | url | error |",
                "|---|---:|---:|---|---|---|",
            ]
        )
        bad_rows = [r for r in url_rows if r.get("traceability_status") != "open"]
        for row in bad_rows[:120]:
            error = compact(row.get("error")).replace("|", "/")
            lines.append(
                f"| {row['traceability_status']} | {row['http_status']} | {row['row_count']} | "
                f"{row['source_orgs']} | {row['url']} | {error} |"
            )
        if not bad_rows:
            lines.append("| 无 | - | - | - | - | - |")

    return "\n".join(lines) + "\n"


def build_summary_payload(audit: dict[str, object], kb_path: Path, headers: list[str], url_rows: list[dict[str, object]] | None) -> dict[str, object]:
    payload = dict(audit)
    payload.pop("problem_rows", None)
    rows_by_source_url = dict(payload.pop("rows_by_source_url", {}))
    payload["rows_by_source_url_items"] = [
        {"source_url": url, "row_count": count} for url, count in sorted(rows_by_source_url.items())
    ]
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["kb_path"] = str(kb_path)
    payload["headers"] = headers
    if url_rows is not None:
        payload["url_status_counts"] = dict(Counter(compact(r.get("traceability_status")) for r in url_rows).most_common())
        payload["url_affected_row_counts"] = {
            status: sum(int(r.get("row_count") or 0) for r in url_rows if compact(r.get("traceability_status")) == status)
            for status in {compact(r.get("traceability_status")) for r in url_rows}
        }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit source traceability for knowledge_base_curated.csv")
    parser.add_argument("--kb", default=str(REPO_ROOT / "knowledge_base_curated.csv"))
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "artifacts/kb_traceability_20260718"))
    parser.add_argument("--check-urls", action="store_true")
    parser.add_argument("--url-limit", type=int, default=0, help="0 means all unique URLs.")
    parser.add_argument("--url-workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--sleep-ms", type=int, default=0)
    parser.add_argument("--ignore-proxy", action="store_true", help="Ignore http_proxy/https_proxy environment variables during URL checks.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kb_path = Path(args.kb).resolve()
    out_dir = Path(args.out_dir).resolve()
    headers, rows = read_csv(kb_path)
    audit = audit_rows(rows)
    out_dir.mkdir(parents=True, exist_ok=True)

    problem_rows = list(audit["problem_rows"])
    problem_csv = out_dir / "kb_traceability_problem_rows.csv"
    write_csv(
        problem_csv,
        ["id", "title", "category", "subcategory", "risk_level", "source_title", "source_org", "source_url", "issues"],
        problem_rows,
    )

    url_rows = None
    url_audit_csv = out_dir / "kb_source_url_audit.csv"
    if args.check_urls:
        urls = sorted(str(u) for u in audit["rows_by_source_url"])
        if args.url_limit > 0:
            urls = urls[: args.url_limit]
        url_results = audit_urls(
            urls,
            timeout=args.timeout,
            workers=args.url_workers,
            cache_path=out_dir / "url_check_cache.json",
            sleep_ms=args.sleep_ms,
            trust_env=not args.ignore_proxy,
        )
        url_rows = build_url_rows(rows, url_results)
        write_csv(
            url_audit_csv,
            [
                "url",
                "traceability_status",
                "http_status",
                "row_count",
                "source_orgs",
                "sample_source_title",
                "sample_ids",
                "final_url",
                "content_type",
                "bytes_sampled",
                "error",
            ],
            url_rows,
        )
    else:
        # Preserve the full-link summary in the Markdown report when the URL audit
        # has already been generated and this run only refreshes row-level checks.
        url_rows = read_url_rows(url_audit_csv)

    payload = build_summary_payload(audit, kb_path, headers, url_rows)
    (out_dir / "kb_traceability_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "kb_traceability_report.md").write_text(render_markdown(audit, url_rows, kb_path), encoding="utf-8")

    print(f"[done] rows={audit['row_count']} unique_urls={audit['unique_source_url_count']}")
    print(f"[done] problem_rows={len(problem_rows)} csv={problem_csv}")
    print(f"[done] report={out_dir / 'kb_traceability_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
