# 项目交接文档 —— 基于 Dify 的实验室安全小助手

> **更新日期**：2026-08-01
> **交接人**：当前维护者  
> **接收人**：后续开发/维护团队  
> **仓库地址**：https://github.com/leilehuimieba/lab-safe-assistant-dify-rag

---

## 〇、2026-08-01 接手前必读

### 0.1 当前工作区状态

- 工作目录：`D:\newwork\Security\lab-safe-assistant-dify-rag`。
- 公开仓库：<https://github.com/leilehuimieba/lab-safe-assistant-dify-rag>。
- 不在交接文档中固化“当前有/无未提交变更”，接手后必须以实时命令为准：

```powershell
git status --short
git branch --show-current
git log -1 --oneline
```

- 私有结项材料在 `docs/conclusion_private/`，该目录已被 `.gitignore` 忽略，不进入 GitHub。
- 旧 `项目结题报告（简版）-龙华秋-送审底稿_20260728.docx` 可能正被 WPS 打开；新的当前版为 `项目结题报告（简版）-龙华秋-送审底稿_20260731_v2.docx` 与同名 PDF。

### 0.2 2026-07-31 / 2026-08-01 已完成的关键收口

1. **NRC 失效来源替换**
   - 原 URL：`https://www.nrc.gov/docs/ML2014/ML20147A696.pdf`。
   - 当前 KB 中已不再出现该 URL，校验结果：`old_url_rows=0`、`old_any_rows=0`。
   - 受影响条目：`KB-RECO-0090`、`KB-RECO-0099`、`KB-RECO-0189`。
   - 替代来源：
     - `https://www.ecfr.gov/current/title-10/chapter-I/part-20`
     - `https://www.federalregister.gov/documents/2014/09/12/2014-21757/applications-of-bioassay-for-radioiodine`
     - `https://www.govinfo.gov/content/pkg/FR-2014-09-12/pdf/2014-21757.pdf`（仅作为引用地址；本机命令行 TLS 下载失败，未声明本地 PDF 原件成功）
   - 处理原则：不是找到了 `ML20147A696` 原件，而是移除当前 KB 对旧失效 PDF 直链的依赖，不以相似 NRC 文档冒充原件。

2. **当前来源覆盖报告更新**
   - 新报告：`docs/eval/source_backup_coverage_20260731.md`。
   - 当前口径：3009 条 KB；717 个唯一来源 URL；1276 个唯一来源标题；344 个可打开；318 个 blocked；52 个 network_error；3 个异常 HTTP 状态。
   - PDF 来源：150 个；本地 PDF 证据副本：150 个；缺口：0 个。
   - 历史 20260725/20260728 的 NRC 失败记录保留，不倒改历史。

3. **覆盖审计状态分项漏计修复**
   - `scripts/audit_source_backup_coverage.py` 的 `summarize_coverage()` 原先只输出 open/blocked/network_error/not_audited 四个状态，`bad_http_status` 被静默丢弃，导致公开报告分项之和为 714、与 717 不符（20260728 那版同样是 713≠716）。
   - 已补 `bad_http_status_urls`、`other_status_urls`、完整 `status_counts`，并加入“分项之和必须等于唯一来源链接总数”的运行时校验；新增 2 个回归测试。
   - `docs/eval/source_backup_coverage_20260731.md` 与同批 summary JSON 已按同一口径回填，未重跑管线，`generated_at` 取证时间戳保持不变。
   - 3 个异常状态均为 csb.gov 的 5xx 网关错误且非 PDF 来源，PDF 150/150 口径不受影响。
   - 20260725/20260728 历史报告按“不倒改历史”原则保持原样。

4. **私有结项报告更新**
   - 新 DOCX：`docs/conclusion_private/项目结题报告（简版）-龙华秋-送审底稿_20260731_v2.docx`。
   - 新 PDF：`docs/conclusion_private/项目结题报告（简版）-龙华秋-送审底稿_20260731_v2.pdf`。
   - 已同步更新 NRC 替换、717 URL、1276 个唯一来源标题、344 open、150/150 PDF 当前口径，并将报告证据日期统一为 2026-07-31。
   - 字体格式沿用官方附件2：标题 22 磅方正小标宋简体，正文 16 磅仿宋，上下左右 2.8 cm 页边距。

5. **完整回答 P95 <3s 实现与部署（2026-08-01）**
   - 新增 `web_demo/services/response_mode_service.py`。默认 `LABSAFE_RESPONSE_MODE=local_complete`：`/api/chat` 在本地结构化 KB、既有快速通道或终端安全规则上完成最终回答，不等待 Dify token 流结束；运维人员可显式设为 `dify` / `dify_only` 使用生成式增强模式。
   - 已部署到远程 `labsafe.service`，服务重启后为 `ActiveState=active`、`NRestarts=0`；服务端备份位于远程 `artifacts/backups/complete_response_mode_20260801_complete_response_mode/`。
   - 2 次预热后 50 题正式 HTTP 实测：200=50/50，完整最终回答=50/50，平均 139.1 ms、P50 140.4 ms、**P95 178.8 ms**、最大 185.6 ms。原始证据：`artifacts/performance/app_complete_response_20260801_50.csv`、`artifacts/performance/app_complete_response_20260801_50.md`。
   - 可复测脚本：`scripts/measure_complete_response_performance.py`。该指标是部署服务回环 HTTP 的完整 JSON 回答；公网浏览器网络时延和人工正确性应另行统计。

### 0.3 已验证命令

```powershell
py -3.14 scripts/quality_gate.py
# Quality gate passed.

py -3.14 -m pytest -q
# 2026-08-01：97 passed, 2 skipped, 6 subtests passed
```

### 0.4 仍不能夸大的口径

- 不说“找到了 NRC `ML20147A696` 原件”；只能说“旧直链不可达，当前 KB 已替换为更通用官方来源”。
- 可以说“默认 `/api/chat` 完整 HTTP 回答 P95=178.8ms（2026-08-01，50/50）”；**不得**说“Dify 完整流 P95<3s”。Dify SSE 首事件 P95=2.136s，完整流 P95=6.506s，必须分别说明。
- 不说“7×24 三个月已完成”；完整周期最早 2026-10-01 才能形成。
- 不说“独立专家已签字”；目前只有 AI 模拟预审和自动回归，真实专家签名/单位意见仍待负责人闭环。
- 不把 `docs/conclusion_private/`、财务、签字页、个人联系方式、远程连接配置提交到 GitHub。

### 0.5 下一步真实闭环事项

1. 由真实专家完成签字评分和整改闭环，不以 AI 模拟预审替代。
2. 由负责人补充真实财务、票据、报销状态与单位意见/学院签章。
3. 按真实日期继续累积 7×24 运行记录，完整三个月最早于 2026-10-01 形成，不补写空档。
4. 若提交公开变更，只提交公开可复现文件；`docs/conclusion_private/` 永不提交。提交前重新运行 `quality_gate.py` 和完整 `pytest`。

---

## 一、项目基本信息

| 项目 | 内容 |
|------|------|
| **项目名称** | 基于 Dify 搭建 RAG 增强的大语言模型实验室安全小助手系统 |
| **项目定位** | 五邑大学大创课题标准版（课题申报项目一），聚焦 RAG 问答与知识库管理 |
| **当前完成度** | 核心原型已可部署、演示与回归；专家签字、财务、线下签章和完整三个月试运行仍待闭环 |
| **核心交付物** | FastAPI 演示应用、3009 条知识库、默认完整回答低时延链路、Dify 工作流集成、安全规则引擎 |

---

## 二、仓库与分支说明

```bash
# 主仓库（已推送）
git@github.com:leilehuimieba/lab-safe-assistant-dify-rag.git

# 本地分支
master                          # 主分支（当前最新）
codex/proposal-alignment-round2-20260522  # 申报书对齐第二轮（已合并到 master）

# 远程分支
origin/master                   # 与本地 master 同步（截至 2026-05-28）
origin/codex/proposal-alignment-round2-20260522
```

**当前基线**：`origin/master` 包含 2026-07-28 的远程部署、高风险线上回归、运行快照回收、Dify SSE 性能取证与 SSE gzip 缓冲修复；NRC `ML20147A696` 来源替换与覆盖审计基线提交为 `cb6b592`，位于 `chore/source-audit-20260731`。后续是否存在未提交、未推送或未合并变更，必须以实时 Git 命令结果为准。

> 隐私边界：结题报告送审稿、签字页、财务明细和个人联系方式仅存放在本地 `docs/conclusion_private/`（已忽略），不得提交到 GitHub。

---

## 三、技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.115.6 + Uvicorn 0.34.0 |
| 前端 | React SPA（构建产物托管于 `web_demo/frontend/dist/`） |
| 大模型编排 | Dify 1.13.0 Docker；远程上游 8080，本地默认 API 8081 |
| 知识库 | 本地 CSV + Dify Dataset 双轨 |
| 数据格式 | CSV、YAML、JSONL |
| 脚本语言 | Python 3.11+、PowerShell |

---

## 四、目录结构速查

```text
lab-safe-assistant-dify-rag/
├── web_demo/                    # FastAPI 演示应用（核心工程）
│   ├── app.py                   # 应用入口
│   ├── models.py                # Pydantic 模型
│   ├── repositories.py          # 数据仓库（KB 加载）
│   ├── routers/
│   │   ├── chat_routes.py       # /api/chat、/api/search、Dify 代理
│   │   ├── meta_routes.py       # /health、/api/meta
│   │   └── kb_router.py         # 知识库可视化（需密码）
│   ├── services/                # 业务逻辑层
│   │   ├── upstream_service.py  # Dify SSE 调用
│   │   ├── response_mode_service.py # 默认完整回答 / 显式 Dify 模式选择
│   │   ├── kb_service.py        # 本地知识库检索
│   │   ├── answer_service.py    # 规则回答/兜底/低置信队列
│   │   ├── response_cache_service.py  # 响应缓存持久化
│   │   └── kb_usage_service.py  # KB 使用统计
│   ├── frontend/dist/           # React SPA 构建产物（已提交）
│   └── templates/index.html     # 简化版问答页面（备用）
├── libs/                        # 通用工具库
├── scripts/                     # 运维/导入/评测脚本
│   ├── start_dify_rag_local.ps1     # 启动服务
│   ├── stop_dify_rag_local.ps1      # 停止服务
│   ├── status_dify_rag_local.ps1    # 查看状态
│   ├── quality_gate.py              # 质量门禁
│   ├── build_runtime_report.py      # 生成运行报告
│   ├── record_runtime_snapshot.py   # 记录运行时快照
│   └── release/import_csv_to_dify_dataset.py  # Dify Dataset 导入
├── docs/                        # 文档集合
│   ├── proposal/                # 申报书相关材料
│   ├── eval/                    # 评测报告（20题/50题/冒烟测试等）
│   ├── ops/                     # 部署说明、用户使用说明
│   └── design/                  # 设计文档（如 kb-viz.md）
├── artifacts/                   # 运行产出（部分已忽略）
│   ├── runtime/                 # ⛔ 已加入 .gitignore（自动生成）
│   ├── screenshots/             # 浏览器截图证据
│   └── dify_import/             # 导入报告
├── data_sources/                # 数据来源
│   └── public_lab_safety_sources_v1.csv   # 外部权威来源种子清单
├── release_exports/             # 各版本发布包
│   ├── v8.2/                    # 原始 398 条主知识库
│   ├── v9_original_claim_3000/  # 3164 条语义切分包（检索粒度优化）
│   ├── v10_external_sources/    # 1159 条外部权威来源
│   └── v12_cornell_3k/          # Cornell 扩展包
├── knowledge_base_curated.csv   # 主知识库（3009 行）
├── safety_rules.yaml            # 安全规则配置
├── eval_set_v1.csv              # 评测题集 v1
├── eval_set_v2_50.csv           # 50 题评测集
├── requirements.txt             # Python 依赖
└── .env.dify_rag.example        # 环境变量模板
```

---

## 五、环境准备与快速启动

### 1. 安装依赖

```powershell
cd D:\newwork\lab-safe-assistant-dify-rag
pip install -r requirements.txt
```

### 2. 配置环境变量

复制模板并填写真实 Dify 配置：

```powershell
cp .env.dify_rag.example .env.dify_rag
```

```env
# .env.dify_rag
DIFY_BASE_URL=http://127.0.0.1:8081
DIFY_APP_API_KEY=app-xxxxxxxxxxxxxxxx
DIFY_TIMEOUT=120

DEMO_PORT=8088
DEFAULT_TOP_K=4
LOW_CONFIDENCE_TOP_SCORE=3.5
KB_IMPORT_SUCCESS_COUNT=398
KB_CHUNK_IMPORT_COUNT=3164
KB_EXTERNAL_IMPORT_COUNT=1159

ENABLE_EMBEDDING=0
SEMANTIC_WEIGHT=12.0
```

### 3. 启动服务

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_dify_rag_local.ps1
```

访问地址：

| 端点 | 地址 |
|------|------|
| 前端页面 | http://127.0.0.1:8088 |
| 健康检查 | http://127.0.0.1:8088/health |
| 元信息 | http://127.0.0.1:8088/api/meta |
| 问答接口 | POST /api/chat |
| 本地检索 | GET /api/search?q=化学品泄漏&top_k=5 |
| KB 可视化 | /kb-viz.html（需密码，见 `.env.web_demo`） |

### 4. 停止服务

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_dify_rag_local.ps1
```

---

## 六、核心功能模块

### 6.1 问答链路（`/api/chat`）

1. 接收用户问题
2. **本地知识库检索**（关键词匹配 + 可选语义匹配）
3. **安全规则匹配**（`safety_rules.yaml`）—— 高风险问题优先走规则引擎
4. **Dify 上游调用**（SSE 流式返回）
5. **结构化兜底** —— 低置信度问题时返回标准模板 + 加入补强队列
6. **响应缓存** —— 命中缓存直接返回，减少上游调用

### 6.2 安全规则引擎

配置文件：`safety_rules.yaml`

- 匹配高风险关键词（如“爆炸”“氰化物”“汞泄漏”）
- 触发规则时返回保守、权威的安全指引，不依赖 LLM 生成
- 已生效，6/20 评测题由规则引擎回答

### 6.3 低置信度补强队列

- 阈值：`LOW_CONFIDENCE_TOP_SCORE=3.5`
- 低于阈值的问题记录到 `artifacts/low_confidence_followups/`
- 后续可人工审核并补充进知识库

### 6.4 运行时监测

- 脚本：`scripts/record_runtime_snapshot.py`
- 数据：`artifacts/runtime/`（CSV + JSONL，**已加入 .gitignore**）
- 报告：`scripts/build_runtime_report.py` 生成周报
- 可注册 Windows 计划任务实现每日自动检查（见 `register_daily_runtime_check.ps1`）

---

## 七、知识库与数据

### 7.1 主知识库

| 文件 | 说明 | 数量 |
|------|------|------|
| `knowledge_base_curated.csv` | 当前主知识库 | **3009 条** |
| `release_exports/v8.2/knowledge_base_import_ready.csv` | 原始 398 条主库（已导入 Dify） | 398 条 |
| `release_exports/v9_original_claim_3000/` | 语义切分包（检索粒度优化，**非独立来源**） | 3164 条 |
| `release_exports/v10_external_sources/` | 外部权威来源（OSHA/NIH/Cornell 等） | 1159 条 |
| `release_exports/v12_cornell_3k/` | Cornell 实验室安全手册扩展 | 约 3000 条级别 |

### 7.2 Dify Dataset 导入状态

| Dataset | ID | 状态 |
|---------|-----|------|
| 实验室安全知识库 | `abdb8a2b-1e56-457a-b55c-c50c76a63eff` | 已导入 398 条，失败 0 条 |
| 实验室安全知识库-外部权威来源扩展版 | （待创建） | 待导入 v10 外部来源 |

导入命令：

```powershell
python scripts/release/import_csv_to_dify_dataset.py `
  --csv release_exports/v10_external_sources/knowledge_base_external_import_ready.csv `
  --base-url http://127.0.0.1:8081 `
  --dataset-id <dataset_id> `
  --dataset-api-key <dataset_api_key>
```

---

## 八、测试与评估

### 8.1 已有评测

| 评测 | 题数 | 结果 | 报告 |
|------|------|------|------|
| 冒烟测试 | — | 通过 | `docs/eval/dify_rag_smoke_test_20260428.md` |
| 正式评测 | 20 | 20/20 HTTP 成功，20/20 有引用 | `docs/eval/eval_20_20260428.md` |
| 扩展评测 | 50 | 人工评分 | `docs/eval/eval_50_human_scored.md` |
| 用户试用 | — | 有记录 | `docs/eval/user_trial_report.md` |

### 8.2 运行评测

```powershell
# 一键运行 20 题评测
python scripts/run_eval_batch.py --csv eval_set_v1.csv --out artifacts/eval/

# 质量门禁
python scripts/quality_gate.py
```

---

## 九、待办事项（已知缺口）

### 高优先级

| 序号 | 事项 | 说明 |
|------|------|------|
| 1 | **Dify 上游恢复** | 本地 Docker/Dify 服务（8081）当前未运行，需恢复后导入 3009 级知识库 |
| 2 | **外部来源导入** | 将 v10 的 1159 条外部来源导入新的 Dify Dataset |
| 3 | **99% 准确率证据** | 需专家人工评分后才能严谨宣称，当前不伪造；已有 50 题人工评分基础 |
| 4 | **响应 <3s 优化** | 已完成：默认 `/api/chat` 完整 HTTP 回答 50/50 成功、P95=178.8ms、最大=185.6ms；Dify SSE 首事件 P95=2.136s、完整流 P95=6.506s，三项不得混用 |

### 中优先级

| 序号 | 事项 | 说明 |
|------|------|------|
| 5 | **7×24 试运行记录** | 监测骨架已建立（`record_runtime_snapshot.py`），需从真实日期开始积累 3 个月 |
| 6 | **3000+ 独立来源口径** | 当前 3009 行含拆分片段，需确保“独立权威来源”数量达标 |
| 7 | **前端完善** | 当前 React SPA 已具备基础功能，可继续增强 |

### 低优先级

| 序号 | 事项 | 说明 |
|------|------|------|
| 8 | 语义检索（Embedding） | 当前关闭（`ENABLE_EMBEDDING=0`），开启需安装 `sentence-transformers` |
| 9 | 多语言支持 | 当前以中文为主 |
| 10 | 与原大创闭环项目整合 | 原项目在 `lab-safe-assistant-workspace/lab-safe-assistant-github` |

---

## 十、交接清单

- [x] 代码已推送至 GitHub（`origin/master` 最新）
- [x] `.gitignore` 已更新（忽略 `artifacts/runtime/` 等自动生成文件）
- [x] 主知识库 `knowledge_base_curated.csv` 已提交（3009 行）
- [x] 环境变量模板 `.env.dify_rag.example` 已提供
- [x] 启动/停止/状态脚本已验证可用
- [x] 申报书相关材料已归档于 `docs/proposal/`
- [x] 评测报告已归档于 `docs/eval/`
- [ ] ⚠️ **Dify Docker 服务需接收方自行恢复**
- [ ] ⚠️ **真实 Dify APP Key 需接收方配置到 `.env.dify_rag`**
- [ ] ⚠️ **KB 可视化密码需接收方在 `.env.web_demo` 中设置**

---

## 十一、关键文件索引

| 目的 | 文件路径 |
|------|----------|
| 快速了解项目 | `README.md` |
| 本交接文档 | `HANDOVER.md` |
| 环境配置模板 | `.env.dify_rag.example` |
| 启动脚本 | `scripts/start_dify_rag_local.ps1` |
| 部署说明 | `docs/ops/部署与运行说明.md` |
| 用户使用说明 | `docs/ops/用户使用说明.md` |
| 申报书正文 | `docs/proposal/申报书_基于Dify的实验室安全小助手_标准课题版.md` |
| 技术路线 | `docs/proposal/技术路线说明_基于Dify的实验室安全小助手.md` |
| 20 题评测 | `docs/eval/eval_20_20260428.md` |
| 运行监测方案 | `docs/ops/原申报书长期运行与性能监测方案_20260522.md` |

---

## 十二、备注

1. **与原项目关系**：本项目是“标准课题版”，聚焦 RAG 问答；原大创闭环项目（风险评估、培训考核、管理看板等）仍在 `lab-safe-assistant-workspace/lab-safe-assistant-github` 中维护。
2. **数据安全**：`.env.dify_rag` 含敏感 Key，**已加入 .gitignore**，切勿手动提交。
3. **运行时数据**：`artifacts/runtime/` 为自动生成监控数据，不纳入版本控制，如需历史记录请单独备份。
4. **Windows 环境**：项目主要在 Windows + PowerShell 环境下开发和运行，部分脚本使用了 Windows 特定路径。

---

> **交接完成确认**：代码已推送到 GitHub，工作树干净，交接文档已归档。接收方可直接克隆仓库并按“快速启动”章节运行。
