# AGENTS.md — 基于 Dify 的实验室安全小助手

> **Version 1.0.0**  
> 面向 AI 代理与协作者  
> 2026-07-01

---

## 1. 项目定位

本项目是一个**大学生创新项目（大创）**原型，基于 **FastAPI + Dify + RAG** 构建的实验室安全问答系统。核心目标：可演示、可验收、可答辩。不是生产级 SaaS，不必过度工程化。

- **主链路**：用户提问 → 本地 KB 检索 / 安全规则匹配 → Dify 上游 SSE 调用 → 结构化回答
- **技术栈**：FastAPI 0.115、React SPA、Dify Docker（本地 8081）、CSV 知识库
- **关键指标**：3009 条结构化知识资产、有效回答率 >95%、响应 <3s、7×24 三个月试运行

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
- 应急类与重点专项的"立即处理/禁止事项/应急升级"结构在 `answer_service.py::_build_emergency_rule_answer` 与 `build_rule_answer` 头部特判中硬编码，覆盖 `R-008, R-011~R-022, R-026, R-027, R-028, R-029, R-030, R-031, R-032` 共 20 条（其中 R-027/R-028/R-029 为 `direct_safe_answer` 但有专用模板）。修改 yaml 不会自动改变这三段，需要同步修改代码或 yaml 的 `response`（结论段）。
- 新增应急规则时，如果 rule_id 不在上述 20 条范围内，会走通用兜底模板，不是硬编码的详细模板。
- `enforcement: always` 对两类 action 都生效：`refuse` 是"命中即拒绝"，`redirect_emergency` 是"命中即按应急处置"。后者只用于 patterns 本身就是事故陈述的规则（R-030 人员失去反应、R-031 低温容器超压、R-032 人员伤害兜底）——这类输入常写成陈述句（"同事昏迷不醒"），句中没有 `EMERGENCY_INTENT_MARKERS`，若不豁免会被判成非应急、进而落到超出服务范围的婉拒模板。给普通应急规则加 `always` 会让它在任何提到该关键词的知识性问题上也按事故作答，不要这么做。
- **人员伤亡一票否决**：`repositories.py::has_casualty_report` 判断问句是否在报告"已经有人受伤/失去反应"。命中时 `assess_out_of_scope` 与 `build_fallback_lab_answer` 一律不得返回"不在服务范围内"，`match_rule` 也把它当作应急意图。错误代价是不对称的——误答"怎么做番茄炒蛋"没有代价，误拒"同事昏迷不醒"是本系统能产生的最坏输出。
- `CASUALTY_INTENT_MARKERS`（`repositories.py`）与 `safety_rules.yaml` 的 R-032 `patterns` 必须逐字一致，由 `tests/test_emergency_rules.py::CasualtyFallbackTests` 断言。只收"已发生的人身伤害/失能状态"，不收裸的危害名词（"烫伤"、"中毒"），否则"烫伤怎么预防"会被按事故作答。
- R-032 `severity: low` 是刻意的：任何意图对齐的专项规则都会压过它，它只在没有专项规则、或专项规则与意图不匹配时兜底。
- **规则在 yaml 里的先后顺序有语义**：`match_rule` 的打分元组以 `-order` 收尾，同分时靠前者胜。R-030 被放在 R-013/R-026（火灾）之后、R-016（误食中毒）之前，就是为了让 critical 级规则按施救顺序排序；移动这些块会改变匹配结果。
- 改动上述任何一处后，跑 `python scripts/scan_casualty_refusals.py`（对抗性扫描，66 条合成伤亡问句，有任何一条被判超范围就退出码 1）并对全库问句重跑 `match_rule` 比较前后差异。

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

### 3.2 文档约定

- `docs/README.md` 是 `docs/` 的**唯一导航入口**，也是唯一需要随仓库状态更新的索引。新增文档必须在那里登记；不要另起第二份索引，否则两份都会烂掉（2026-08-04 整理前它已停留在 2026-06-09，完全没提 `docs/conclusion_2026/`）。
- 带日期的文档是**当时的证据快照**：不回填、不改写、不删除。同一题材因此会有多份文件名相近的文档，这是规范要求的结果，不是重复文件。要表达"情况变了"，写一份新日期的，并在 `docs/README.md` 里把"当前有效"指过去。
- 因此**几乎没有文档可以删**：已提交的结项/申报材料按路径互相引用，删任何一份都会打断引用链。清理文档 = 更新索引，不是删文件。
- 当前口径（规则条数、KB 行数、性能数字）只在 `README.md` 第 0 节和 `docs/README.md` 第 3 节维护，其他文档里的历史数字保持原样。

### 3.3 禁止行为

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
- 答辩口径：项目形成了 3009 条结构化知识片段，来源覆盖 717 个独立机构、1276 份权威文献与规范。
- v9 的 3164 条是“398 条切片”，不能作为新增独立来源口径。

### 5.3 验收指标
- “99% 准确率”必须分层举证：项目自评 100%（L1/L2/L3）+ 专家评审 ≥95%（L4）。不承诺整体 3009 条准确率 99%。
- 性能口径必须分链路：默认 `LABSAFE_RESPONSE_MODE=local_complete` 的 `/api/chat` 完整 HTTP 回答可按“完整回答 P95<3s”统计；2026-08-01 的 50 题部署服务实测为 P95=178.8ms。**Dify SSE 首字节 <3s**与 **Dify 完整流** 是另一组指标（2026-07-28：首事件 P95=2.136s、完整流 P95=6.506s），不得混用或写成“Dify 完整回答<3s”。
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
