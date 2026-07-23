# 人工 URL 复查说明

- 生成日期：2026-07-18
- 来源审计文件：`artifacts/kb_traceability_20260718/kb_source_url_audit.csv`
- 复查对象：自动脚本未判定为 `open` 的 URL
- 全量清单：`manual_url_review_all_non_open_20260718.csv`
- 优先清单：`manual_url_review_priority_top80_20260718.csv`
- 域名汇总：`manual_url_review_by_domain_20260718.csv`

## 当前范围

| 类型 | URL 数 | 说明 |
|---|---:|---|
| `blocked_or_forbidden` | 337 | 多为 401/403/429、反爬、地区策略、Cloudflare 或站点权限策略 |
| `network_error` | 39 | 多为远端重置、连接超时、TLS/证书或网络路径异常 |
| 合计 | 376 | 这些链接不能写成“脚本可打开”，但也不能直接等同于死链 |

## 复查填写口径

建议在 CSV 的 `manual_result` 填以下枚举之一：

| manual_result | 使用场景 |
|---|---|
| `browser_open` | 浏览器可直接打开正文或 PDF，标题/内容与 `sample_source_title` 基本一致 |
| `browser_open_after_challenge` | 浏览器出现人机验证或安全检查，完成后可打开正文或 PDF |
| `official_but_blocked` | 能确认是官方页面，但浏览器仍被 403/Cloudflare/权限策略拦截 |
| `login_or_paid_required` | 需要登录、订阅、购买或机构权限，不适合作为核心验收来源 |
| `cert_error` | 浏览器提示证书错误、域名不匹配或不安全连接 |
| `not_found_or_removed` | 浏览器也返回 404/410/页面不存在 |
| `topic_mismatch` | 页面可打开，但主题与知识片段不匹配 |
| `needs_replacement` | 虽能打开或可识别，但不稳定、不权威或不适合结项现场展示 |
| `uncertain` | 暂时无法判断，需二次核验 |

`evidence_note` 建议写一句短证据，例如：

- `Chrome 可打开 PDF，标题为 OSHA Laboratory Safety Guidance`
- `打开后进入 Cloudflare 验证页，未进入正文`
- `页面要求机构登录`
- `页面标题与知识片段主题不一致`

## 优先复查顺序

先复查 `manual_url_review_priority_top80_20260718.csv`，再看全量清单。优先级依据是影响片段数、是否为权威来源、是否可能在答辩现场被点开。

### 第一组：OSHA / CDC / NCBI / openstd 高影响来源

| 影响片段 | 状态 | 链接 |
|---:|---|---|
| 133 | 403 | `https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1450` |
| 47 | network_error | `https://www.ncbi.nlm.nih.gov/books/NBK55873/` |
| 29 | 403 | `https://www.osha.gov/sites/default/files/publications/OSHA3404LABORATORY-SAFETY-GUIDANCE.pdf` |
| 27 | 403 | `https://www.cdc.gov/labs/BMBL.html` |
| 23 | 403 | `https://www.osha.gov/laser-hazards/hazards` |
| 14 | 403 | `https://www.cdc.gov/mmwr/preview/mmwrhtml/su6101a1.htm` |
| 13 | network_error | `https://openstd.samr.gov.cn/` |
| 10 | 403 | `https://documents.thermofisher.com/TFS-Assets/CMD/manuals/Man-4820-3601-LC-Vanquish-UHPLC-Man48203601-EN.pdf` |
| 9 | 403 | `https://www.osha.gov/workers/employer-responsibilities` |
| 8 | network_error | `https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=EB3B94B543F6E4CD18C044DE6AB64CEC` |
| 8 | 403 | `https://www.cdc.gov/labs/bmbl/` |
| 7 | network_error | `https://www.ncbi.nlm.nih.gov/books/NBK55878/` |
| 7 | 403 | `https://www.nrc.gov/reading-rm/doc-collections/cfr/part020/` |
| 7 | 403 | `https://www.nrc.gov/about-nrc/radiation/protects-you/protection-principles.html` |
| 7 | 403 | `https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200` |
| 7 | 403 | `https://www.osha.gov/hazcom/appendix-c` |

### 第二组：Agilent 网络异常来源

Agilent 官方站点在脚本环境下大量远端重置，但已有两个代表性 PDF 通过真实 Chrome 抽样打开。建议你按全量清单里 `domain=www.agilent.com` 的 27 个 URL 抽查 8-10 个即可，重点看 PDF 是否能直接打开、标题是否对应。

优先抽查：

| 影响片段 | 链接 |
|---:|---|
| 3 | `https://www.agilent.com/cs/library/usermanuals/public/7890B_Safety.pdf` |
| 2 | `https://www.agilent.com/cs/library/usermanuals/public/user-manual-gcms-hydrogen-safety-q7003-90053-en-agilent.pdf` |
| 2 | `https://www.agilent.com/cs/library/primers/public/Best_Practice_LC_Operations.pdf` |
| 2 | `https://www.agilent.com/cs/library/usermanuals/public/7890A%20GC%20User%20Manual%20Collection.pdf` |
| 1 | `https://www.agilent.com/cs/library/sitepreparationchecklists/7800_7900_ICP-MS_Site_Preparation_Checklist_Rev.B.pdf` |
| 1 | `https://www.agilent.com/cs/library/sitepreparationchecklists/Agilent%208890%20GC%20Site%20Preparation%20Checklist.pdf` |

### 第三组：需要重点判断是否替换的来源

这些不是都必须删除，但如果人工复查结果不理想，应优先替换为更稳定的官方或高校 EHS 来源：

| 域名 | URL 数 | 影响片段 | 建议 |
|---|---:|---:|---|
| `pubs.acs.org` | 2 | 3 | 若需要订阅或机构权限，不作为核心验收来源 |
| `webstore.ansi.org` | 2 | 2 | 商业标准入口不适合作为唯一来源，建议补法规或公开指南 |
| `manualmachine.com` | 1 | 4 | 第三方手册站，优先找厂商原始 PDF |
| `makesafetyeasy.com` | 1 | 3 | 第三方博客/材料，优先替换为 OSHA/NFPA/高校 EHS |
| `coactionspecialty.safetynow.com` | 1 | 1 | 第三方页面，若无法打开或主题弱，建议替换 |

## 人工复查后如何回填

1. 打开 `manual_url_review_priority_top80_20260718.csv`。
2. 对每条 URL 填写 `manual_result`、`manual_access_time`、`reviewer`、`evidence_note`。
3. 若判断需要替换，在 `recommended_action` 写目标，例如 `replace_with_ecfr`、`replace_with_official_pdf`、`replace_with_university_ehs`。
4. 复查完成后，把 CSV 留在同目录；后续可按 `manual_result` 批量更新结项说明或继续替换知识库来源。
