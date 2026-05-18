# 运行复核记录（2026-05-16）

> 项目：基于 Dify 搭建 RAG 增强的大语言模型实验室安全小助手系统  
> 复核时间：2026-05-16  
> 项目路径：`D:\newwork\lab-safe-assistant-dify-rag`

## 1. 本轮结论

本轮已完成一次基于当前仓库的真实运行复核，结论如下：

1. 本地 Web Demo 已成功恢复运行，监听地址为 `http://127.0.0.1:8091`；
2. `scripts/start_dify_rag_local.ps1` 可正常启动服务，并生成运行时文件 `artifacts/local-dify-rag/runtime.json`；
3. 质量门禁 `scripts/quality_gate.py` 在当前可用 Python 环境下通过；
4. `/health`、`/api/meta`、`/api/search`、`/api/chat` 均可返回成功响应；
5. 当前 `http://127.0.0.1:8081` 的 Dify 后台/API 仍未监听，因此普通问题会降级走 `structured_fallback`，高风险问题仍由本地规则引擎稳定拦截或应急引导；
6. 因此项目当前状态应表述为：**本地演示链路可用，Dify 上游暂不可用，安全兜底链路可工作。**

## 2. 本轮执行动作

### 2.1 启动状态复核

通过以下脚本确认并恢复本地运行状态：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/status_dify_rag_local.ps1
powershell -ExecutionPolicy Bypass -File scripts/start_dify_rag_local.ps1
```

复核到的关键运行信息：

- 启动时间：`2026-05-16T23:59:57`
- 访问地址：`http://127.0.0.1:8091`
- 运行 PID：`48744`
- Python：`D:\Grammar\python\python.exe`
- 日志：`D:\newwork\lab-safe-assistant-dify-rag\logs\dify_rag.log`
- 错误日志：`D:\newwork\lab-safe-assistant-dify-rag\logs\dify_rag.err.log`

### 2.2 质量门禁复核

由于系统默认 `python` 环境缺少 `fastapi`，直接执行会失败；改为复用启动脚本解析出的 Python 解释器后，质量门禁通过：

```powershell
& D:\Grammar\python\python.exe scripts/quality_gate.py --repo-root .
```

结果：

```text
Quality gate passed.
```

## 3. 接口复核结果

### 3.1 健康检查

- 地址：`http://127.0.0.1:8091/health`
- 结果：HTTP 200
- 返回：

```json
{"status":"ok"}
```

### 3.2 元信息接口

- 地址：`http://127.0.0.1:8091/api/meta`
- 结果：HTTP 200

关键字段摘要：

- `app_version`: `dify-rag-project-1`
- `acceptance_status`: `project-1-extracted`
- `formal_eval_score`: `20/20`
- `stability_status`: `3/3 PASS`
- `knowledge_base_rows`: `142`
- `knowledge_base_imported`: `398`
- `knowledge_base_chunked`: `3164`
- `knowledge_base_external`: `1159`
- `demo_port`: `8091`
- `dify_base_url`: `http://127.0.0.1:8081/v1`
- `dify_app_key_configured`: `true`

### 3.3 本地检索接口

- 地址：`GET http://127.0.0.1:8091/api/search?q=化学品泄漏&top_k=3`
- 结果：HTTP 200

摘要：

- 返回引用数：`3`
- Top1 命中：`KB-1052 / 未知化学品泄漏时先做什么`
- Top1 来源：`高等学校实验室安全规范 / 教育部`

### 3.4 高风险问答复核

测试问题：

> 实验室发生化学品泄漏应该怎么做？

结果摘要：

- 结果：HTTP 200
- `model`: `rule-engine`
- `decision`: `emergency_redirect`
- `matched_rule_id`: `R-015`
- `risk_level`: `high`

说明：高风险问题在 Dify 不可用时仍能通过本地规则引擎给出应急引导和引用依据，符合安全兜底预期。

### 3.5 普通问答复核

测试问题：

> 进入化学实验室前通常需要佩戴哪些个人防护装备？

结果摘要：

- 结果：HTTP 200
- `model`: `fallback-rule-engine`
- `decision`: `structured_fallback`
- 返回体中包含：`fallback reason: upstream unavailable`

说明：这说明当前普通问题没有实际走通 Dify 上游，而是降级到结构化兜底回答。此现象与本机 `8081` 未监听的现状一致。

## 4. 上游状态判断

本轮实际探测结果：

- `http://127.0.0.1:8091`：可访问；
- `http://127.0.0.1:8081`：连接被拒绝；
- Dify 上游工作流：当前不可用；
- 本地 KB 检索、规则判断、结构化兜底：可用。

因此当前不应写成“Dify 主链路已恢复”，更准确的口径应为：

> 当前本地 RAG 演示服务已恢复；Dify 上游仍未恢复，系统可通过本地知识检索与规则/结构化兜底继续提供安全问答演示。

## 5. 对项目推进的影响

### 已确认可继续推进的内容

1. 本地演示、截图、录屏、接口联调；
2. 文档归档与验收补证；
3. 本地知识库检索与规则链路验证；
4. 外部来源扩展包的导入准备工作；
5. 低风险的 UI / 文案 / 展示层优化。

### 当前仍受阻的内容

1. Dify workflow 主链路真实回归；
2. 外部权威来源 1159 条导入 Dify Dataset；
3. 基于 Dify 上游的真实性能复测；
4. “Dify 已恢复可用”的验收口径更新。

## 6. 下一步建议

建议按以下顺序继续推进：

1. 先恢复 `http://127.0.0.1:8081` 的 Dify 后台/API；
2. Dify 恢复后，重新执行普通问题问答复核，确认 `model` 回到 `dify-workflow`；
3. 执行外部来源导入：

```powershell
python scripts/release/import_csv_to_dify_dataset.py `
  --csv release_exports/v10_external_sources/knowledge_base_external_import_ready.csv `
  --base-url http://127.0.0.1:8081 `
  --dataset-id <外部来源Dataset_ID> `
  --dataset-api-key <dataset_api_key> `
  --skip-existing `
  --sleep-ms 5 `
  --report-json artifacts/dify_import_external_sources/import_report.json `
  --report-md docs/eval/dify_import_external_sources_report.md
```

4. 导入完成后，再补一轮：
   - `20` 题正式回归；
   - 引用命中核查；
   - 平均耗时 / P95 复测；
   - Dataset 索引完成状态截图。

## 7. 本轮证据文件

- 运行时文件：`D:\newwork\lab-safe-assistant-dify-rag\artifacts\local-dify-rag\runtime.json`
- 启动日志：`D:\newwork\lab-safe-assistant-dify-rag\logs\dify_rag.log`
- 错误日志：`D:\newwork\lab-safe-assistant-dify-rag\logs\dify_rag.err.log`
- 外部来源待导入报告：`D:\newwork\lab-safe-assistant-dify-rag\docs\eval\dify_import_external_sources_report.md`

