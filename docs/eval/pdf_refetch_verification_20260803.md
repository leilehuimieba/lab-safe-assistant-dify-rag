# 31 个 PDF 来源重抓复核与下载器缺陷修复（2026-08-03）

## 1. 结论先说

本轮**没有改变任何覆盖口径**。PDF 来源仍为 **150** 个、有本地 PDF 证据副本 **150** 个、缺口 **0** 个，与 2026-07-31 一致。

本轮的实际价值是三件事：一是证实了此前被怀疑为"只有记录、没有真文件"的 31 个 PDF 来源**确实早已存在完整的本地原件**；二是用一次全新的直连下载对其中 29 个做了 SHA-256 逐字节复核；三是暴露并修复了下载器里两个会产生错误结论的缺陷。

## 2. 起因与实际发现

本轮起因是怀疑 2026-07-31 口径中有 31 个 PDF 来源属于"ghost"——被计入 `has_local_pdf=yes`，但没有真实文件支撑。

复核后这个怀疑不成立。这 31 个来源的本地原件自 2026-04-29 公开采集轮起就存在于 `artifacts/web_ingest_public_20260429/raw/`，`source_backup_coverage_20260731/source_backup_coverage.csv` 的 `local_paths` 列一直指向这些文件。逐个用 `pypdf` 打开复核，31 个全部是完整、可解析的 PDF，页数从 1 页到 604 页不等（含 CDC/NIH 两版 BMBL6 全文各 604 页）。该目录下 36 个 PDF 整体复核也是 0 个损坏。

因此本轮重抓属于**重复取证**，不是补缺。

## 3. 重抓与逐字节比对结果

对这 31 个来源在 2026-08-03 重新发起直连下载，并与 2026-04-29 的本地副本比对 SHA-256：

| 结果 | 数量 | 说明 |
|---|---:|---|
| 与 2026-04-29 副本 SHA-256 完全一致 | **29** | 新鲜直连下载逐字节复现历史归档，历史副本的真实性得到独立印证 |
| 本轮未抓完，未纳入证据 | **2** | `chemical-safety-guide.pdf`（38.9 MB）、`cryogen-fact-sheet.pdf`（6.4 MB） |

两个未抓完的来源不是被拦截，而是 `ors.od.nih.gov` 在本机网络下实测吞吐仅约 7 KB/s，38.9 MB 的文件按此速率需数小时。**截断文件已删除**，manifest 中这两行标记为 `refetch_incomplete` 而非 `downloaded`；它们的权威本地原件仍是 2026-04-29 那份完整副本，本轮只是没有再复核一遍。

比对明细见 `artifacts/pdf_source_backups_20260803/refetch_vs_20260429_cache.csv`。

## 4. 过程中发现并修复的两个下载器缺陷

这两个缺陷都会让 `scripts/download_missing_pdf_backups.py` 得出错误结论，且都已在本轮实测中触发。

### 4.1 `%PDF-` 头部校验会把截断文件当成功（假阳性）

原校验只检查响应开头是否为 `%PDF-`。但被 `--max-time` 掐断的传输同样以 `%PDF-` 开头，只是文件是半截的。本轮首次落盘的 NIH BMBL6 只有 15,292 字节却通过了校验——真实文件是 4,559,461 字节、604 页；`pypdf` 打开时报 `Cannot find Root object in pdf`。同批共 4 个文件是这种"看着成功、其实半截"的状态。

修复方式是增加 `is_complete_pdf()`：在 `%PDF-` 头之外，要求文件尾部 2 KB 内存在 `%%EOF` 结束标记。该判据在全部 150 个已存备份上与 `pypdf` 的判定完全一致（150/150 相符），因此不需要引入解析器依赖。

同时增加断点续传：检测到"有 PDF 头但无 `%%EOF`"时用 HTTP Range 续传（`curl --continue-at -`）最多 6 轮，而不是丢弃半截文件重来。NIH BMBL6 正是靠续传补完的。

### 4.2 落地页跳转被误判为"源已失效"（假阴性）

9 个 Yale EHS 来源在首轮返回 HTML，被记为 `response was not a PDF`，据此很容易得出"Drupal 改版后直链失效"的结论。实测不是这样：

```
https://ehs.yale.edu/sites/default/files/files/laser-sop.pdf
  → 301 → https://ehs.yale.edu/resource/laser-standard-operating-procedure   （落地页）
  → 落地页内 <a href="/resource/download/382">Download</a>
  → https://ehs.yale.edu/resource/download/382   HTTP 200, application/pdf, 144,569 字节
```

文件仍在发布，只是从直链改成了"落地页 + `/resource/download/{id}`"。9 个 Yale 来源全部如此，跟一跳即可取回。修复方式是增加 `pdf_links_in_html()`：当响应是 HTML 时，从页面中提取 `**/download/<数字>` 或 `.pdf` 链接（排除 `/css/`、`/js/`），跟随**一跳**后再判定；仍取不到才记为失败。

### 4.3 顺带修复：HTTP 状态码正则

`_parse_headers` 前身的正则写成 `r"^HTTP/\\S+\\s+(\\d+)"`。raw string 里 `\\S` 是"字面反斜杠 + S"，不是 `\S`，因此 curl 分支记录的 `http_status` 恒为空——2026-07-25 那批 80 条 manifest 的 `http_status` 全空即由此而来。已改为 `\S`/`\s`/`\d` 并补了断言。

## 5. 证据文件

| 文件 | 内容 |
|---|---|
| `artifacts/pdf_source_backups_20260803/pdf_backup_manifest_20260803.csv` | 第一轮原始记录（18 成功 / 13 失败），保留不动以维持审计链 |
| `artifacts/pdf_source_backups_20260803/pdf_backup_retry_manifest_20260803.csv` | 第二轮逐条记录，含 Yale 跳转后的真实下载地址 |
| `artifacts/pdf_source_backups_20260803/pdf_backup_manifest_20260803_final.csv` | 合并表，新增 `index`/`pass`/`pdf_pages` 三列；`sha256`、`size_bytes` 按落盘文件重算 |
| `artifacts/pdf_source_backups_20260803/refetch_vs_20260429_cache.csv` | 重抓副本与 2026-04-29 副本的 SHA-256 逐条比对 |
| `artifacts/pdf_backup_integrity_20260803.csv` | 三个备份目录 148 个文件的完整性复核，`pypdf` 可读性逐条记录，当前 0 损坏 |
| `docs/eval/source_backup_coverage_20260803.md` | 纳入本轮 manifest 后重算的覆盖审计 |

## 6. 口径与遗留

- 覆盖口径不变：**150 个 PDF 来源，150 个有本地 PDF 证据副本，缺口 0**。不能表述为"本轮新增了 PDF 原件"。
- 本轮 29 个来源是**真正意义上的原始 URL 直连下载**（`backup_kind=direct_original`），可按 2026-07-28 第 4 条口径称为原件直连；其余仍按 `archive_replay` / `institutional_mirror` 如实标注。
- NRC `ML20147A696` 维持 2026-07-31 处置：本轮用 curl 复测仍是 HTTP 403（WAF 拦截，返回 404 字节的 HTML），未恢复原件，相关 3 条知识已改由 eCFR 10 CFR Part 20 与 RG 8.20 支撑。
- `docs/eval/pdf_backup_retry_40_20260728.md` 记录的是当日早些时候那次尝试（0 成功），当天稍后的 Wayback 重放轮实际取回 39/40。该文档已补加说明，避免被单独引用时误读。
- 与本轮无关的既有失败：`tests/test_emergency_rules.py::test_metal_sodium_storage_uses_water_reactive_guidance` 在 HEAD 上即失败（期望 `R-027`，实得 `R-026`），本轮未改动相关代码，也未修复。
