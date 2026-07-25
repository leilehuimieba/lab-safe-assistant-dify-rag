# PDF 原件本地备份补档执行记录（2026-07-25）

> 目的：针对结项证据中“PDF 和本地证据留存”短板，优先下载现有知识库来源 URL 中缺失的 PDF 原件，并记录可复核的本地路径、SHA-256、文件大小和剩余缺口。财务数据不在本文范围内。

## 1. 执行摘要

本轮以 `artifacts/source_backup_coverage_20260725/source_backup_coverage.csv` 中标记为 `is_pdf_source=yes` 且 `has_local_pdf=no` 的 120 个 PDF 来源为对象，按影响知识片段数优先处理。

| 指标 | 补档前 | 本轮新增 | 补档后 |
|---|---:|---:|---:|
| PDF 来源总数 | 151 | - | 151 |
| 有本地 PDF 原件的来源 | 31 | 58 | 89 |
| 缺本地 PDF 原件的来源 | 120 | -58 | 62 |
| 有本地原件或官方镜像证据的 URL | 93 | +58 | 151 |
| 被本地证据覆盖的知识片段 | 1474 | +134 | 1608 |

本轮实际保存并索引的 PDF 文件 58 个，对应 58 个唯一来源 URL。全部保存文件均做 `%PDF-` 文件头校验，并生成 SHA-256 索引。

## 2. 新增文件与索引

| 材料 | 路径 | 用途 |
|---|---|---|
| PDF 原件目录 | `artifacts/pdf_source_backups_20260725/files/` | 保存本轮下载的 PDF 原件。 |
| PDF 文件索引 | `artifacts/pdf_source_backups_20260725/pdf_backup_file_index_20260725.csv` | 记录 source_url、local_path、SHA-256、文件大小和索引时间。 |
| PDF 文件索引摘要 | `artifacts/pdf_source_backups_20260725/pdf_backup_file_index_summary_20260725.json` | 汇总本轮 PDF 文件数、唯一 URL 数和覆盖率。 |
| 下载脚本 | `scripts/download_missing_pdf_backups.py` | 可复现地下载缺失 PDF，并避免把 HTML/错误页伪装为 PDF。 |
| PDF 索引脚本 | `scripts/index_pdf_backups.py` | 扫描本地 PDF 目录，按 source_url 哈希重建 manifest/索引/摘要。 |
| 替代 URL 记录 | `artifacts/pdf_source_backups_20260725/pdf_url_replacements_20260725.csv` | 记录旧 URL、同机构/同厂商现行下载端点、替换理由和本地 PDF 路径。 |
| 覆盖审计脚本 | `scripts/audit_source_backup_coverage.py` | 已更新，可扫描新 PDF 备份目录并计入覆盖率。 |

## 3. 下载策略

1. 只对现有知识库中已经出现的 PDF 来源 URL 补原件，不随意引入非权威转载。
2. 优先处理 `traceability_status=open` 且 `content_type=application/pdf` 的来源。
3. 使用 Windows `curl.exe`、PowerShell `Invoke-WebRequest`、长时重试、`--ssl-no-revoke`、MSYS2/OpenSSL curl 等多种方式下载。
4. 下载后必须校验文件头包含 `%PDF-`；如果返回 HTML、验证码、403 页面或空文件，则记录为失败，不计入本地 PDF 原件。
5. 对站点策略阻断、TLS EOF、网络错误的来源，不伪造原件；能找到同机构新版/下载端点的，单独记录替代 URL 与替换理由。

## 4. 本轮主要成功补档示例

- Stanford `lab-chemical-safety-plan.pdf`
- Agilent ICP-MS `G8400-90016_Precautions.pdf`、`G3666-90006_Precautions.pdf`
- Thermo Fisher `Summit-UG.pdf`、`GC-MS Q Exactive` 手册、多个安全/应用说明 PDF
- UNT `tga_2_user_manual.pdf`
- Stanford `Storage-Group-Poster.pdf`
- IAEA `Pub1578_web-57265295.pdf`
- Pitt Chemistry `safety-manual.pdf`
- 北京大学医学部实验室安全手册 PDF
- Agilent 多个 GC/LC/MS 手册与安全清单、Metrohm 89308001EN 手册
- Yale Biological Safety Manual、University of Guelph Laboratory Safety Manual 2025 现行下载端点
- Shimadzu、SCIEX、Renishaw、Weizmann、SLU、UWindsor 等设备/安全相关 PDF

详细清单以 `artifacts/pdf_source_backups_20260725/pdf_backup_file_index_20260725.csv` 为准。

## 5. 剩余缺口说明

补档后仍有 62 个 PDF 来源缺本地 PDF 原件，主要原因包括：

1. OSHA PDF：本地 curl/Node/Chrome/in-app browser 均出现 403 或 `ERR_CONNECTION_CLOSED`；但 `web.open` 能验证部分 PDF 在线存在，例如 OSHA 3404 Laboratory Safety Guidance。
2. NIH Guidelines：本地下载 403；`web.open` 可验证 PDF 在线存在。
3. CDC/EPA/NRC 部分 PDF：自动审计显示可打开，但本机下载时多次出现 TLS handshake/EOF/timeout，换用 Schannel、`--ssl-no-revoke` 和 OpenSSL curl 后仍失败。
4. Berkeley 等个别 PDF URL 返回 HTML 包装页，不直接返回 PDF 原件，需要浏览器人工下载或替换为同机构可下载的新链接；Yale 与 Guelph 已通过同机构现行下载端点补齐。
5. Thermo/OSHA 等个别设备手册或官方文件仍存在站点防护、迁移或区域访问限制，需要官方站内搜索或产品文档页替代；Agilent 与 Metrohm 已新增补齐一批。

因此，当前严谨口径是：**89/151 个 PDF 来源已有本地 PDF 原件，仍缺 62 个；部分缺口已能在线验证存在，但本机无法保存原始 PDF，需要后续人工下载、浏览器导出或官方镜像替代。**


## 5.1 已在线验证但尚未形成本地 PDF 原件的高影响来源

以下来源经 `web.open` 验证可作为在线 PDF 访问，但本机 `curl`、Node fetch 或浏览器自动化下载失败，因此**不计入本地 PDF 原件覆盖数**，仅作为后续人工下载/换网络下载的优先清单：

| 影响片段 | 来源 | 在线验证 | 本机下载状态 |
|---:|---|---|---|
| 29 | OSHA Laboratory Safety Guidance | `web.open` 返回 `application/pdf`，52 页 | 403 / connection closed |
| 6 | EPA Hazardous Waste Characteristics | `web.open` 返回 `application/pdf`，30 页 | TLS EOF / handshake failed |
| 5 | NIH Guidelines | `web.open` 返回 `application/pdf`，132 页 | 403 |
| 5 | OSHA 3088 Workplace Emergencies and Evacuations | `web.open` 返回 `application/pdf`，30 页 | 403 |
| 4 | CDC/NIOSH School Chemistry Laboratory Safety Guide | `web.open` 返回 `application/pdf`，86 页 | TLS EOF / handshake failed |

明细文件：`artifacts/pdf_source_backups_20260725/online_verified_unbacked_pdf_sources_20260725.csv`。

## 6. 结项口径更新

旧口径：31/151 个 PDF 来源有本地 PDF 原件，仍缺 120 个。

新口径：89/151 个 PDF 来源有本地 PDF 原件，仍缺 62 个。

可用于答辩的表述：

> 项目已完成一轮 PDF 原件本地补档，本地 PDF 原件覆盖由 31/151 提升到 89/151，新增 58 个唯一 PDF 来源原件，并为每个文件记录 SHA-256、大小和本地路径。剩余 62 个 PDF 来源主要受站点防护、TLS 握手失败或 HTML 包装页影响，已列入后续人工下载、浏览器验证或官方镜像替代清单。

## 7. 后续建议

1. 对 OSHA/NIH 这类 `web.open` 可访问但本机无法下载的官方 PDF，保留网页访问验证截图或使用其他网络环境人工下载。
2. 对 CDC/EPA/NRC TLS EOF 类链接，换用校园网、VPN、浏览器“另存为”或官方 archive/stacks/govinfo 镜像继续补档。
3. 对设备厂商手册迁移链接，优先从厂商官网产品文档页找同版本或新版 PDF，不使用非权威转载替代。
4. 若替换知识库 source_url，应保留原 URL、替代 URL、替换理由、替换时间和审核人。
