# 剩余 40 个 PDF 原件补档重试（2026-07-28）

> **本文只记录当日早些时候的直连重试轮，结论已被同日后续轮次取代。** 当天稍后的 Wayback 重放/机构镜像轮实际取回 39/40，仅 NRC `ML20147A696` 未取回，覆盖口径随之由 111/151 变为 150/151（见 `artifacts/pdf_source_backups_20260728/pdf_backup_summary_20260728.json` 与 `docs/eval/source_backup_coverage_20260728.md`）。单独引用本文的"新增 0、仍缺 40"会得出过时结论。

- 输入：2026-07-25 覆盖审计中仍缺本地原件的 40 个 PDF 来源。
- 执行：逐 URL 尝试 HTTPS/HTTP、小范围 URL 编码变体、两种 User-Agent 和 PowerShell 回退；所有成功候选必须通过 `%PDF-` 文件头校验后才能收录。
- 结果：尝试 40，新增有效 PDF 0，失败 40。
- 证据：`artifacts/pdf_source_backups_20260728/pdf_backup_manifest_20260728.csv` 逐条记录错误与时间戳。

本轮没有把 HTML 错误页、WAF 页面或空文件冒充 PDF 原件，因此本地覆盖仍为 151 个 PDF 来源中 111 个已有原件、40 个待补。部分链接可由网页阅读器打开，但当前本机下载链路受 TLS/CDN/WAF 限制；后续需校园网/VPN、官方站内替代链接或人工浏览器下载，并继续记录 SHA-256 和最终 URL。

执行结束时发现脚本对“相对输出目录”的汇总路径处理会抛出 `ValueError`；40 条 manifest 已在异常前完整写入。该缺陷已增加回归测试并修复，未重新发起 40 次重复网络请求。
