# AGENTS.md — 基于 Dify 的实验室安全小助手

> **Version 1.0.0**  
> 面向 AI 代理与协作者  
> 2026-07-01

---

## 1. 项目定位

本项目是一个**大学生创新项目（大创）**原型，基于 **FastAPI + Dify + RAG** 构建的实验室安全问答系统。核心目标：可演示、可验收、可答辩。不是生产级 SaaS，不必过度工程化。

- **主链路**：用户提问 → 本地 KB 检索 / 安全规则匹配 → Dify 上游 SSE 调用 → 结构化回答
- **技术栈**：FastAPI 0.115、React SPA、Dify Docker（本地 8081）、CSV 知识库
- **关键指标**：3000+ 知识库、有效回答率 >95%、响应 <3s、7×24 三个月试运行

---

## 2. 致命 Bug 检查清单（每次修改必查）

### 2.1 并发与异步

- **async 路由中禁止直接调用同步 IO**（`requests.post`, `requests.get` 等）。如果路由是 `async def`，必须用 `run_in_threadpool` 包装，或改用 `httpx.AsyncClient`。
- **FastAPI 的 `def` 路由会自动在线程池中执行**，这是安全的。`async def` 路由才会直接跑在事件循环上。

### 2.2 SSRF 与网络边界

- `resolve_dify_api_base()` 已启用 **host 白名单**（默认 `127.0.0.1`, `localhost`, `::1`）。如果部署环境需要其他 host，通过 `DIFY_ALLOWED_HOSTS` 环境变量显式配置。
- `build_dify_proxy_auth()` **禁止透传入站 `Authorization`**。只能使用服务器端配置的 `DIFY_APP_API_KEY`。
- 上游代理接口（`/v1/parameters`, `/v1/chat-messages`）不要把入站请求任意转发到未校验的 URL。

### 2.3 资源泄漏

- 每次 `requests.post(..., stream=True)` 或 `requests.get(...)` 后必须调用 `.close()`，或使用 `try/finally` 确保关闭。
- SSE 流式响应（StreamingResponse）的迭代器必须在 `finally` 中关闭上游连接。

### 2.4 Schema 一致性

- 知识库 CSV 表头修改必须同步到 `libs/kb_schema.py`。
- `KB_HEADERS`（29 列）是权威定义，`DIFY_IMPORT_FIELDS`（25 列）自动排除内部字段 `id/last_updated/reviewer/status`。
- `scripts/quality_gate.py` 会校验实际 CSV 表头与 `KB_HEADERS` 是否一致。

### 2.5 安全规则引擎

- `safety_rules.yaml` 中的 `rule.response` 只影响**结论段**。
- `R-011~R-020`（应急类）的“立即处理/禁止事项/应急升级”结构在 `answer_service.py::_build_emergency_rule_answer` 中硬编码。修改 yaml 不会自动改变这三段，需要同步修改代码或 yaml 的 `response`（结论段）。
- 新增应急规则时，如果 rule_id 不在 `R-011~R-020` 范围内，会走通用兜底模板，不是硬编码的详细模板。

---

## 3. 仓库整理规范

### 3.1 文件层级

```
根目录只保留权威文件：
README.md, HANDOVER.md, knowledge_base_curated.csv, safety_rules.yaml,
eval_set_v2_50.csv, requirements.txt, AUDIT_GUIDE.md, DATA_COLLECTION_SPEC.md, DATA_RECOLLECTION_PLAN.md

其他产物按规则放：
- scripts/_archive/    — 一次性生成脚本（已归档，保留 git 历史）
- artifacts/          — 运行时产出、评测报告、导入报告
- release_exports/    — 当前版本保留，老版本 zip 到 _archive/
- docs/               — 所有文档、评测记录、申报书材料
```

### 3.2 禁止行为

- 禁止在根目录留下 `.tmp_*`, `*_report.md`, `*_list.csv`, `audit_sample.csv` 等一次性中间产物。
- 禁止把敏感信息（`.env.dify_rag` 含 App Key）提交到 git。已加入 `.gitignore`。
- 禁止追溯造假运行数据。`artifacts/runtime/` 的监控数据从真实日期开始累积，不倒填。

---

## 4. 提交规范

- 英文提交信息，格式：`type: concise description`
- 常见 type：`feat`, `fix`, `docs`, `chore`, `refactor`, `test`
- 大规模清理用 `chore:`，功能性修复用 `fix:`，新增文档用 `docs:`
- 如果一次修改涉及多个维度（如本次对抗式审查），允许使用多行提交信息，但第一行必须概括全貌。

---

## 5. 常见陷阱与认知纠偏

### 5.1 端口
- 代码默认端口是 **8081**（Dify API），不是 8080。`.env.dify_rag.example` 和 `repositories.py` 都已对齐。如果看到 8080，是漂移，必须改。

### 5.2 知识库口径
- 3009 条是**结构化片段**，不是 3009 条独立文档。答辩话术应强调“3000+ 结构化片段，来自 400+ 权威来源”。
- v9 的 3164 条是“398 条切片”，不能作为新增独立来源口径。

### 5.3 验收指标
- “99% 准确率”必须分层举证：项目自评 100%（L1/L2/L3）+ 专家评审 ≥95%（L4）。不承诺整体 3009 条准确率 99%。
- “<3s 响应”指 **Dify SSE 首字节 <3s**。本地 fast_path 完整回答 <300ms，Dify 完整回答 P95 <10s。
- “7×24 三个月”从 **2026-07-01** 起算，用 `record_runtime_snapshot.py` 累积真实运行数据，不倒填。

### 5.4 评审追问防御
- 评委问“随机抽 20 条给我看 source_url”—— 确保 `source_url` 字段非空且可访问。
- 评委问“规则怎么维护”—— 展示 `safety_rules.yaml` 单一文件 + `updated_at` 字段，说明 72h 同步机制。
- 评委问“Dify 挂了怎么办”—— 展示本地 KB 检索兜底 + 结构化 fallback 回答。

---

## 6. AI 代理协作备忘

- 每次修改后运行 `git status` 确认变更范围，避免误删 tracked 文件。
- 修改 `safety_rules.yaml` 时同步检查 `answer_service.py` 的硬编码模板是否需要调整。
- 修改 CSV 字段时同步更新 `libs/kb_schema.py`，并运行 `scripts/quality_gate.py` 验证。
- 涉及网络请求的修改，必须检查是否引入了新的同步 IO 阻塞或 SSRF 风险。
- 环境变量 `.env.dify_rag` 含敏感信息，**绝不**写入代码或提交到 git。

---

> 本文档基于 2026-07-01 对抗式审查（Claude 会话 d6f5e7ee）的结论整理。后续如需调整，追加版本号和新文件，不覆盖本版。
