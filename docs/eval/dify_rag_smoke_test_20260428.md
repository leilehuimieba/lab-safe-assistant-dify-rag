# Dify RAG Smoke 测试报告

> 报告日期：2026-04-28  
> 项目路径：`D:\newwork\lab-safe-assistant-dify-rag`  
> 测试地址：`http://127.0.0.1:8091`  
> 测试类型：最小运行与问答链路 smoke test  

## 1. 测试结论

本次 smoke 测试通过。系统已完成本地启动、健康检查、元信息读取、本地知识库检索、高风险规则响应和一次真实 Dify 工作流调用验证。

关键结论：

1. 本地服务已启动，端口为 `8091`；
2. Dify App Key 已配置，`/api/meta` 返回 `dify_app_key_configured=true`；
3. `/health` 返回正常；
4. `/api/search` 能返回知识库引用；
5. 高风险应急问题能触发 `emergency_redirect`；
6. 禁止类问题能触发 `rule_blocked`；
7. 常规强酸安全问题成功调用 Dify，返回 `model=dify-workflow`。

---

## 2. 运行证据

| 项目 | 内容 |
|---|---|
| 启动时间 | `2026-04-28T16:12:43` |
| 服务地址 | `http://127.0.0.1:8091` |
| 进程 PID | `8744` |
| Dify 配置 | `True` |
| 环境文件 | `D:\newwork\lab-safe-assistant-dify-rag\.env.dify_rag` |
| 启动脚本生成文件 | `D:\newwork\lab-safe-assistant-dify-rag\artifacts\local-dify-rag\launch_dify_rag.py` |
| 标准日志 | `D:\newwork\lab-safe-assistant-dify-rag\logs\dify_rag.log` |
| 错误日志 | `D:\newwork\lab-safe-assistant-dify-rag\logs\dify_rag.err.log` |
| Smoke 原始结果 | `artifacts/smoke/smoke_20260428.json` |

说明：环境文件中包含 Dify App Key，不应提交到公开仓库或公开展示。

---

## 3. 基础接口结果

| 接口 | HTTP 状态 | 耗时 ms | 结果 |
|---|---:|---:|---|
| `/health` | 200 | 168.32 | `{'status': 'ok'}` |
| `/api/meta` | 200 | 25.97 | Dify Key 配置：`True`；Dify 地址：`http://127.0.0.1:8081/v1` |
| `/api/search?q=化学品泄漏&top_k=5` | 200 | 9.35 | 命中 `5` 条引用 |

---

## 4. 问答 Smoke 结果

| 序号 | 问题 | HTTP 状态 | 耗时 ms | decision | model | 引用数 | 判定 |
|---:|---|---:|---:|---|---|---:|---|
| 1 | 实验室发生化学品泄漏时，第一步应该怎么做？ | 200 | 52.44 | `emergency_redirect` | `rule-engine` | 4 | 通过 |
| 2 | 使用强酸时需要注意什么？ | 200 | 10431.73 | `dify_answer` | `dify-workflow` | 4 | 通过 |
| 3 | 实验废液可以直接倒入下水道吗？ | 200 | 35.86 | `rule_blocked` | `rule-engine` | 4 | 通过 |

---

## 5. 典型回答摘要

### 1. 实验室发生化学品泄漏时，第一步应该怎么做？

- decision：`emergency_redirect`
- model：`rule-engine`
- citations：`4`
- answer preview：结论: / 若发生化学品泄漏：隔离现场、避免接触和吸入，在安全前提下通风并使用泄漏应急物资处理，立即报告实验室管理人员。 /  / 步骤: / 1. 立即停止当前操作并隔离危险源。 / 2. 第一时间通知实验室负责人和安全联系人。 / 3. 按本单位 SOP 执行现场控制、上报和记录。 /  / 禁止事项: / - 禁止继续开展当前高风险操作。 / - 禁止

### 2. 使用强酸时需要注意什么？

- decision：`dify_answer`
- model：`dify-workflow`
- citations：`4`
- answer preview：使用强酸时需佩戴护目镜、实验服、耐酸手套。操作必须在通风柜内进行，注意前窗高度和风速正常。一旦溅到皮肤，立即大量清水冲洗，脱去污染物并就医。

### 3. 实验废液可以直接倒入下水道吗？

- decision：`rule_blocked`
- model：`rule-engine`
- citations：`4`
- answer preview：结论: / 危废需按制度分类收集，禁止随意排放。 /  / 步骤: / 1. 立即停止当前操作并隔离危险源。 / 2. 第一时间通知实验室负责人和安全联系人。 / 3. 按本单位 SOP 执行现场控制、上报和记录。 /  / 禁止事项: / - 禁止继续开展当前高风险操作。 / - 禁止绕过通风、审批、联锁或 PPE 要求。 /  / 应急升级: / - 如存在受伤、起

---

## 6. 指标汇总

| 指标 | 结果 |
|---|---:|
| 基础接口测试数 | 3 |
| 基础接口通过数 | 3 |
| 问答测试数 | 3 |
| 问答成功响应数 | 3 |
| 成功响应率 | 100% |
| 有引用回答数 | 3 |
| 引用返回率 | 100% |
| 高风险/禁止类测试数 | 2 |
| 高风险/禁止类合规响应数 | 2 |
| 高风险合规响应率 | 100% |
| Dify 工作流成功调用数 | 1 |
| 本地规则响应数 | 2 |

---

## 7. 本次测试覆盖和未覆盖范围

### 已覆盖

1. 本地 FastAPI 服务启动；
2. `/health` 健康检查；
3. `/api/meta` 元信息与 Dify 配置状态；
4. `/api/search` 本地知识库检索；
5. `/api/chat` 高风险应急响应；
6. `/api/chat` 常规问题真实 Dify 工作流调用；
7. `/api/chat` 禁止类问题规则拦截。

### 未覆盖

1. 尚未做多日连续运行验证；
2. 尚未做人工评分版有效回答率统计；
3. 尚未验证 Dify 后台工作流每个节点的详细配置截图；
4. 尚未做 3 个月试运行记录。

---

## 8. 后续建议

1. Dify Dataset 已完成正式导入，报告见 `docs/eval/dify_import_report.md`；
2. 已从 `eval_set_v1.csv` 中抽取 20 题并形成正式评测报告：`docs/eval/eval_20_20260428.md`；
3. 已截图保存首页、问答页和检索结果：`artifacts/screenshots/`；
4. 如果用于最终验收，建议保持当前 8091 端口，或在释放 8088 后恢复默认端口。


---

## 9. 浏览器截图证据

本次测试已保存浏览器级截图，用于证明页面可访问、问答可用、引用可展示。

| 截图 | 路径 | 说明 |
|---|---|---|
| 首页状态 | `artifacts/screenshots/dify_rag_home.png` | 展示项目首页和 Dify 配置状态 |
| 问答结果 | `artifacts/screenshots/dify_rag_chat.png` | 展示“使用强酸时需要注意什么？”的 Dify/RAG 问答结果 |
| 检索结果 | `artifacts/screenshots/dify_rag_search.png` | 展示“化学品泄漏”的本地知识库检索结果 |


---

## 10. 20 题正式评测证据

已补充 20 题正式评测。

| 项目 | 结果 |
|---|---:|
| 评测题数 | 20 |
| HTTP 成功 | 20/20 |
| 有引用回答 | 20/20 |
| Dify 工作流回答 | 14 |
| 规则引擎回答 | 6 |
| 结构化兜底回答 | 0 |
| 平均耗时 | 4614.21 ms |
| 最大耗时 | 16149.6 ms |

证据文件：

- `docs/eval/eval_20_20260428.md`
- `artifacts/eval_20/eval_20_20260428.json`

---

## 11. Dify Dataset 导入状态

Dify Dataset 已完成正式导入。

| 项目 | 结果 |
|---|---:|
| Dataset | `实验室安全知识库` |
| Dataset ID | `abdb8a2b-1e56-457a-b55c-c50c76a63eff` |
| 创建文档数 | 398 |
| 跳过重复数 | 0 |
| 失败数 | 0 |
| 当前索引 total | 398 |
| P95 响应时间 | 9648.34 ms |

证据文件：

- `docs/eval/dify_import_report.md`
- `artifacts/dify_import/import_report.json`


---

## Dify Dataset 正式导入完成记录

- Dataset name：`实验室安全知识库`
- Dataset id：`abdb8a2b-1e56-457a-b55c-c50c76a63eff`
- 导入包：`release_exports/v8.2/knowledge_base_import_ready.csv`
- 创建文档数：`398`
- 跳过重复数：`0`
- 失败数：`0`
- 导入报告：`docs/eval/dify_import_report.md`
- 原始 JSON：`artifacts/dify_import/import_report.json`
