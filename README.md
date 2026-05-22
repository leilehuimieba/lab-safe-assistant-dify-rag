# 基于 Dify 的实验室安全小助手（项目一）

本仓库是从 `D:\newwork\lab-safe-assistant-workspace\lab-safe-assistant-github` 抽离出的**第一个项目**，只保留“基于 Dify 搭建 RAG 增强的大语言模型实验室安全小助手系统”所需的最小代码与材料。

## 0. 2026-05-22 当前快照

- 对照目标文档：`D:\大创\2026大创实验室智能体项目\五邑大学实验室安全课题申报立项书（版本4）(1).docx`
- 当前建议文档入口：`docs/README.md`
- 工程主体完成度（按“可演示可验收原型”口径）：**约 85%—90%**
- 高目标完成度（按版本4立项书全部指标口径）：**约 60%**
- 当前最关键的新增进展：`knowledge_base_curated.csv` 已达到 **3009** 行，本地结构化知识规模已跨过 `3000+` 门槛
- 当前最主要的未完成项：
  1. Dify `8081` 上游恢复与 3k 级正式导入；
  2. `99%` 专业准确率证据；
  3. 平均响应 `<3s`；
  4. `7×24` 与 `3` 个月试运行记录。

## 1. 项目边界

本项目聚焦：

1. Dify 应用 / 工作流调用；
2. 实验室安全 RAG 知识库；
3. 本地知识检索与引用展示；
4. 安全规则约束与高风险保守响应；
5. 低置信问题补强队列；
6. 基础测试、导入与申报材料。

本项目**不包含**原大创闭环项目中的以下扩展模块：

- 风险评估；
- 开工前检查与阻断；
- 培训考核；
- 管理端看板；
- 事故复盘；
- 复杂试点闭环材料。

这些能力仍留在原项目中：

`D:\newwork\lab-safe-assistant-workspace\lab-safe-assistant-github`

## 2. 目录结构

```text
lab-safe-assistant-dify-rag/
├─ web_demo/                     # 最小 FastAPI 演示应用
│  ├─ app.py
│  ├─ models.py
│  ├─ repositories.py
│  ├─ routers/
│  │  ├─ chat_routes.py          # /api/chat、/api/search、Dify 代理接口
│  │  └─ meta_routes.py          # /、/health、/api/meta
│  ├─ services/
│  │  ├─ upstream_service.py      # Dify SSE 调用与输出清洗
│  │  ├─ kb_service.py            # 本地知识库检索与规则匹配
│  │  ├─ answer_service.py        # 规则回答、结构化兜底、低置信队列
│  │  ├─ llm_output_service.py
│  │  └─ meta_service.py
│  └─ templates/index.html        # 简化后的 Dify/RAG 问答页面
├─ libs/                         # 通用 I/O、文本处理、可选 embedding
├─ scripts/
│  ├─ start_dify_rag_local.ps1
│  ├─ status_dify_rag_local.ps1
│  ├─ stop_dify_rag_local.ps1
│  ├─ quality_gate.py
│  └─ release/import_csv_to_dify_dataset.py
├─ docs/proposal/standard_from_doc.docx
├─ knowledge_base_curated.csv
├─ safety_rules.yaml
├─ eval_set_v1.csv
├─ .env.dify_rag.example
└─ requirements.txt
```

## 3. 快速运行

```powershell
cd D:\newwork\lab-safe-assistant-dify-rag
pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/start_dify_rag_local.ps1
```

首次运行会从 `.env.dify_rag.example` 创建 `.env.dify_rag`。
如需真实走 Dify，请填写：

```env
DIFY_BASE_URL=http://127.0.0.1:8080
DIFY_APP_API_KEY=app-xxxxxxxxxxxxxxxx
DIFY_TIMEOUT=120
```

启动后访问：

- 页面：`http://127.0.0.1:8088`
- 健康检查：`http://127.0.0.1:8088/health`
- 元信息：`http://127.0.0.1:8088/api/meta`
- 问答接口：`POST http://127.0.0.1:8088/api/chat`
- 本地检索：`GET http://127.0.0.1:8088/api/search?q=化学品泄漏&top_k=5`

停止：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_dify_rag_local.ps1
```

查看状态：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/status_dify_rag_local.ps1
```

## 4. Dify 知识库导入

如果需要把 CSV 导入 Dify Dataset，可使用迁移过来的导入脚本：

```powershell
python scripts/release/import_csv_to_dify_dataset.py `
  --csv release_exports/v8.2/knowledge_base_import_ready.csv `
  --base-url http://127.0.0.1:8080 `
  --dataset-id <dataset_id> `
  --dataset-api-key <dataset_api_key> `
  --report-json artifacts/dify_import/import_report.json `
  --report-md docs/eval/dify_import_report.md
```

如果本地 Dify 使用 Docker/Postgres，并且需要自动探测 dataset 或自动生成 token，可参考脚本参数：

```powershell
python scripts/release/import_csv_to_dify_dataset.py --help
```

## 5. 当前迁移口径

本次抽离是“最小可运行搬迁”，核心原则是：

- 保留 Dify/RAG 主链路；
- 保留本地 KB 检索，方便显示引用和做兜底；
- 保留安全规则，避免高风险问题不受控；
- 删除大创闭环功能依赖，降低第一个项目复杂度；
- 保留 `standard_from_doc.docx`，方便继续按申报书完成项目一材料。

## 6. 与原项目关系

原项目：

`D:\newwork\lab-safe-assistant-workspace\lab-safe-assistant-github`

继续作为“大创优化版 / 实验室安全闭环管理原型”。

本项目：

`D:\newwork\lab-safe-assistant-dify-rag`

只作为“标准课题版 / 基于 Dify 的 RAG 实验室安全问答系统”。


## 7. 按申报书完善后的当前成果

本项目已按母版申报书：

`D:
ewwork\lab-safe-assistant-workspace\standard_from_doc.docx`

完成标准课题版项目内容整理。当前不再按“大创闭环平台”扩展，而是聚焦申报书题目中的核心主线：

> 基于 Dify 搭建 RAG 增强的大语言模型实验室安全小助手系统。

已补齐的申报书支撑材料包括：

| 类别 | 文件 |
|---|---|
| 母版申报书正文提取 | `docs/proposal/standard_from_doc_extracted_utf8.txt` |
| 标准课题版申报书 | `docs/proposal/申报书_基于Dify的实验室安全小助手_标准课题版.docx` |
| 申报书内容稿 | `docs/proposal/申报书_基于Dify的实验室安全小助手_标准课题版.md` |
| 申报书落实说明 | `docs/proposal/申报书落实版_项目完善说明_20260428.md` |
| 栏目对照整改表 | `docs/proposal/申报书栏目对照整改表_20260428.md` |
| 技术路线说明 | `docs/proposal/技术路线说明_基于Dify的实验室安全小助手.md` |
| 课题总结报告 | `docs/proposal/课题总结报告_基于Dify的实验室安全小助手_20260428.md` |
| Smoke 测试报告 | `docs/eval/dify_rag_smoke_test_20260428.md` |
| 20 题正式评测 | `docs/eval/eval_20_20260428.md` |
| Dify 导入成功报告 | `docs/eval/dify_import_report.md` |
| 部署说明 | `docs/ops/部署与运行说明.md` |
| 用户说明 | `docs/ops/用户使用说明.md` |
| 浏览器截图 | `artifacts/screenshots/` |

当前 20 题正式评测结果：

- 评测题数：20；
- HTTP 成功：20/20；
- 有引用回答：20/20；
- Dify 工作流回答：14；
- 规则引擎回答：6；
- 结构化兜底回答：0。

Dify Dataset 已正式导入：已创建 `实验室安全知识库` Dataset，Dataset ID 为 `abdb8a2b-1e56-457a-b55c-c50c76a63eff`，并成功导入 398 条知识库文档，失败 0 条。


## 8. 原始申报书高目标推进状态（已纠偏）

> 纠偏说明：此前生成的 `release_exports/v9_original_claim_3000/knowledge_base_import_ready_3000.csv` 是把 398 条长文档按语义片段切成 3164 条，用于提升 Dify 检索粒度；它**不等同于新增 3000+ 条独立高质量知识来源**，不能作为原始申报书“3000+ 知识库”完全达成的证据。

当前已改为从公开权威来源继续补真实数据：

| 项目 | 当前状态 |
|---|---|
| 原 398 条主知识库 | 已导入 Dify Dataset `实验室安全知识库`，created=398, failed=0 |
| 3164 条拆分包 | 定位为“长文档语义切分 / 检索粒度优化包”，不再作为真实新增来源口径 |
| 真实外部权威来源扩展 | 已从 OSHA、NIH、CDC/NIH、NCBI Bookshelf、Cornell、Yale、UC Berkeley 等公开来源采集生成 1159 条新增外部条目 |
| 外部来源种子清单 | `data_sources/public_lab_safety_sources_v1.csv` |
| 外部来源导入 CSV | `release_exports/v10_external_sources/knowledge_base_external_import_ready.csv` |
| 外部来源采集报告 | `release_exports/v10_external_sources/import_bundle_report_external.md` |
| 原始抓取与抽取证据 | `artifacts/web_ingest_public_20260429/` |
| 20 题正式评测 | 20/20 成功，20/20 有引用 |
| 高风险安全规则 | rule-engine 已生效 |
| 99% 准确率 | 需要专家人工评分后才能严谨宣称，当前不伪造 |
| 响应 <3 秒 | 当前尚未稳定达到，已列入性能优化目标 |
| 7×24 与 3 个月试运行 | 已建立监测方案，需从真实日期开始积累运行记录 |

新增外部采集证据文件：

- `scripts/ingest_public_lab_safety_sources.py`
- `data_sources/public_lab_safety_sources_v1.csv`
- `release_exports/v10_external_sources/knowledge_base_external_import_ready.csv`
- `release_exports/v10_external_sources/import_bundle_report_external.md`
- `release_exports/v10_external_sources/import_bundle_report_external.json`
- `artifacts/web_ingest_public_20260429/raw/`
- `artifacts/web_ingest_public_20260429/extracted_text/`
- `docs/eval/public_source_link_check_20260429.md`
- `docs/eval/public_pdf_processing_report_20260429.md`

保留但降级说明的检索粒度优化包：

- `release_exports/v9_original_claim_3000/knowledge_base_import_ready_3000.csv`
- `release_exports/v9_original_claim_3000/import_bundle_report_3000.md`
- `docs/eval/dify_import_3000_report.md`
- `artifacts/dify_import_3000/import_report.json`

下一步应将 v10 外部来源包导入单独 Dify Dataset：`实验室安全知识库-外部权威来源扩展版`。当前本机 Docker/Dify 服务未运行时无法执行导入；服务恢复后可直接使用 `scripts/release/import_csv_to_dify_dataset.py` 导入。
