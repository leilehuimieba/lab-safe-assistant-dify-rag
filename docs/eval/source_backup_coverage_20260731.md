# 知识库来源链接与本地备份覆盖审计（2026-07-31）

- 生成时间（UTC）：`2026-07-31T05:37:20.539210+00:00`
- 知识片段：**3009** 条；唯一来源链接：**717** 个；唯一来源标题：**1276** 个
- 当前审计口径可打开：**344** 个；被站点/反爬拦截：**318** 个；网络错误：**52** 个；异常 HTTP 状态：**3** 个；未审计：**0** 个（344+318+52+3+0 = 717，与唯一来源链接总数对平）
- 有本地原件或归档证据：**212** 个链接，覆盖 **1750** 条知识片段
- PDF 来源：**150** 个；有本地 PDF 证据副本：**150** 个；缺本地 PDF 证据：**0** 个

## 结论口径

1. `blocked_or_forbidden` 只表示自动化访问被站点策略拦截，不能直接判定链接失效；需要浏览器抽样或更换官方镜像复核。
2. `network_error` 是当前网络下未完成验证的来源，不能算作已通过。
3. `archive_replay`、官方规范化地址和机构镜像均保留在清单的 `backup_kind`/`attempted_url` 中；这些副本不能冒充原始 URL 的实时直连下载。
4. 只有 `backup_kind=original` 才能称为原始 URL 直连原件；其余只能称为归档/镜像证据副本。
5. 2026-07-31 对 NRC `ML20147A696` 的处理不是“找到原件”，而是删除当前 KB 对该失效旧 PDF 直链的依赖，并用更通用的官方法规/指南来源替换；3 条受影响知识的回答已收紧到 10 CFR 20.1502、20.2003、20.2108、Appendix B Table 3 与 RG 8.20 Revision 2 公告能够支撑的范围。
6. `bad_http_status` 表示服务器返回了非 2xx/非 403 的异常状态码，与 `blocked_or_forbidden`、`network_error` 一样不能直接判定链接失效，需后续复测。

## 异常 HTTP 状态明细（3 个）

此前版本的汇总行遗漏了本状态，导致分项之和为 714、与 717 不符；本版已补齐，明细如下。三条均为 csb.gov 的服务端 5xx 网关错误，且均非 PDF 来源，因此不影响“PDF 来源 150 个、本地 PDF 证据副本 150 个”的口径。

| 影响片段 | HTTP 状态 | 来源链接 |
|---:|---|---|
| 3 | 520 | https://www.csb.gov/csb-releases-investigation-into-2010-texas-tech-laboratory-accident-case-study-identifies-systemic-deficiencies-in-university-safety-management-practices/ |
| 1 | 504 | https://www.csb.gov/csb-releases-new-video-on-laboratory-safety-at-academic-institutions/ |
| 1 | 504 | https://www.csb.gov/statement-from-csb-chairperson-rafael-moure-eraso-on-high-school-laboratory-fire-in-new-york-city-/ |

## PDF 证据缺口（按影响片段数排序）

当前口径下无 PDF 证据缺口。NRC `ML20147A696` 旧 PDF 直链已从当前 KB `source_url` 移除，涉及 3 条知识改由 eCFR 10 CFR Part 20 与 Federal Register/govinfo RG 8.20 公告支撑；历史失败记录仍保留在 2026-07-25/2026-07-28 证据中。
