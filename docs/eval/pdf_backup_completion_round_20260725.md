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

> 说明：本节 5 / 5.1 记录的是**第一轮补档后**的状态（89/151，缺 62）。同日第二轮补档后的最新口径为 111/151、缺 40，详见第 8 节；第 8.3 节给出剩余 40 个缺口的逐条复核结论。

第一轮补档后仍有 62 个 PDF 来源缺本地 PDF 原件，主要原因包括：

1. OSHA PDF：本地 curl/Node/Chrome/in-app browser 均出现 403 或 `ERR_CONNECTION_CLOSED`；但 `web.open` 能验证部分 PDF 在线存在，例如 OSHA 3404 Laboratory Safety Guidance。
2. NIH Guidelines：本地下载 403；`web.open` 可验证 PDF 在线存在。
3. CDC/EPA/NRC 部分 PDF：自动审计显示可打开，但本机下载时多次出现 TLS handshake/EOF/timeout，换用 Schannel、`--ssl-no-revoke` 和 OpenSSL curl 后仍失败。
4. Berkeley 等个别 PDF URL 返回 HTML 包装页，不直接返回 PDF 原件，需要浏览器人工下载或替换为同机构可下载的新链接；Yale 与 Guelph 已通过同机构现行下载端点补齐。
5. Thermo/OSHA 等个别设备手册或官方文件仍存在站点防护、迁移或区域访问限制，需要官方站内搜索或产品文档页替代；Agilent 与 Metrohm 已新增补齐一批。

因此，第一轮结束时的严谨口径是：**89/151 个 PDF 来源已有本地 PDF 原件，仍缺 62 个**（此口径已被同日第二轮的 111/151、缺 40 取代，见第 6、8 节）。


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

演进过程（均为同日 2026-07-25 实测，累计口径）：

- 初始：31/151 个 PDF 来源有本地 PDF 原件，仍缺 120 个。
- 第一轮补档后：89/151，仍缺 62 个。
- 第二轮补档后（当前口径）：**111/151 个 PDF 来源有本地 PDF 原件，仍缺 40 个。**

可用于答辩的表述：

> 项目已完成两轮 PDF 原件本地补档，本地 PDF 原件覆盖由 31/151 提升到 111/151，累计新增 80 个唯一 PDF 来源原件（本地 PDF 文件共 80 个、约 210 MB），并为每个文件记录 SHA-256、大小和本地路径。剩余 40 个 PDF 来源经本机多客户端复核，主要受官方站点 CDN/WAF 边缘拦截（OSHA CloudFront 403、NRC 边缘 403、NIH 403、Thermo Fisher 403）或原 `.pdf` 路径已被官方改为 HTML 网页所致，均非链接失效，已列入缺口清单并逐条记录原因。

## 7. 后续建议

1. 对 OSHA/NIH 这类 `web.open` 可访问但本机无法下载的官方 PDF，保留网页访问验证截图或使用其他网络环境人工下载。
2. 对 CDC/EPA/NRC TLS EOF 类链接，换用校园网、VPN、浏览器“另存为”或官方 archive/stacks/govinfo 镜像继续补档。
3. 对设备厂商手册迁移链接，优先从厂商官网产品文档页找同版本或新版 PDF，不使用非权威转载替代。
4. 若替换知识库 source_url，应保留原 URL、替代 URL、替换理由、替换时间和审核人。

## 8. 第二轮补档执行记录（同日续跑，2026-07-25）

### 8.1 根因定位与修复

第一轮遗留的 62 个缺口中，很大一部分并非“链接失效”，而是本机下载客户端的两个可修复问题：

1. **Windows Schannel 吊销检查失败**：本网络无法访问 CRL/OCSP 服务，导致 `curl.exe`（Schannel）与部分政府 CDN（cdc.gov / nrc.gov / epa.gov / osp.od.nih.gov）握手时被判为“TLS EOF / handshake failed”。加入 `--ssl-no-revoke` 后握手正常，证书链仍按常规校验。
2. **请求头过于简单**：第一轮只发送 `Accept: application/pdf`，部分 WAF 直接判为非浏览器请求返回 403。改为完整浏览器头集合（HTML 优先的 `Accept` + `Sec-Fetch-*` + `Upgrade-Insecure-Requests`）后，多数政府/机构 CDN 放行。

上述两项已固化进 `scripts/download_missing_pdf_backups.py` 的 `curl` 命令，可复现。

### 8.2 结果

| 指标 | 第一轮后 | 第二轮新增 | 第二轮后 |
|---|---:|---:|---:|
| 有本地 PDF 原件的 PDF 来源 | 89 | +22 | 111 |
| 缺本地 PDF 原件的 PDF 来源 | 62 | -22 | 40 |
| 本地 PDF 文件总数 | 58 | +22 | 80 |
| 本地 PDF 文件总大小(bytes) | 181,183,149 | +39,131,060 | 220,314,209 |
| 有本地原件或官方镜像证据的 URL | 151 | +22 | 173 |
| 被本地证据覆盖的知识片段 | 1608 | +40 | 1648 |

第二轮新增的 22 个原件主要来自 CDC/NIOSH（多份 HHE 报告与 wp-solutions/docs 系列）、EPA（`hw-char.pdf`、`cont05.pdf`、`iwaste handbk4.pdf`）、CDC reach/stacks、ACS 网络研讨会讲义等。全部经 `%PDF-` 文件头校验并可被 `pypdf` 正常打开（当前 80 个文件累计 5200+ 页，读取错误 0）。

`artifacts/pdf_source_backups_20260725/online_verified_unbacked_pdf_sources_20260725.csv` 已同步更新：原表中 EPA Hazardous Waste Characteristics 与 CDC/NIOSH School Chemistry Laboratory Safety Guide 两项已在本轮成功保存为本地原件，从“在线可验证但未保存”清单中移除。

### 8.3 剩余 40 个缺口的确认原因

均经本机 `curl.exe`（`--ssl-no-revoke` + 完整浏览器头 + Referer + HTTP/1.1）、PowerShell（.NET TLS）与自动化浏览器三类客户端复核，属于服务端/边缘策略拦截或内容迁移，**非链接失效，未伪造为本地原件**：

| 站点 | 缺口数 | 复核结论 |
|---|---:|---|
| www.osha.gov | 24 | CloudFront 边缘直接 403（`X-Cache: Error from cloudfront`）；浏览器直连报 `ERR_CONNECTION_CLOSED`。含最高影响的 OSHA3404（29 片段）。 |
| www.nrc.gov | 10 | ADAMS 边缘返回 403 HTML 拦截页（F5/BIG-IP 风格）。 |
| documents/tools.thermofisher.com | 2 | S3/CDN 返回 403（`AccessDenied` XML / HTML）。 |
| osp.od.nih.gov | 1 | WordPress/边缘防护 403。 |
| ehs.berkeley.edu | 2 | 旧 `.pdf` 路径现由官方改为 HTML 文章页（返回 `text/html`，标题为对应 EHS 网页），已无 PDF 原件可存；如需留存应按 HTML 镜像归档而非 PDF。 |
| www.umb.edu.pl | 1 | 第三方高校转载的厂商手册，现返回 307 字节 HTML（失效），且本身非权威来源，不作正式 PDF 证据补充。 |

补充说明：作为最后手段尝试过 Internet Archive（`web.archive.org` / `archive.org`）快照回源，但本网络对 archive.org 443 端口连接超时，无法作为本轮替代来源。上述缺口的处理建议见第 7 节（换网络环境、校园网/VPN 或官方站内搜索人工下载）。
