# 技术路线说明：基于 Dify 的实验室安全小助手

> 项目名称：基于 Dify 搭建 RAG 增强的大语言模型实验室安全小助手系统  
> 项目路径：`D:\newwork\lab-safe-assistant-dify-rag`  
> 文档用途：支撑标准课题版申报书中的“课题设计论证”“研究方法”“技术路线”“预期成果”等部分。  

## 1. 项目技术定位

本项目面向高校实验室安全知识服务场景，采用 Dify 平台和 RAG（Retrieval-Augmented Generation，检索增强生成）技术，构建一个可演示、可复用、可继续扩展的实验室安全智能问答原型系统。

系统重点解决以下问题：

1. 实验室安全资料分散，人工查询效率低；
2. 学生和实验人员对 SOP、MSDS、危化品处置和应急流程理解不一致；
3. 通用大模型容易出现无依据回答，缺少知识来源追溯；
4. 高风险实验问题需要安全规则约束，不能直接输出危险操作建议；
5. 低置信问题需要沉淀到后续知识库补强流程。

本项目不是完整实验室安全管理平台，也不包含培训考核、管理看板、事故复盘等大创扩展模块。其核心边界是：

> Dify 工作流 + 实验室安全知识库 + RAG 问答 + 安全规则约束 + 引用追溯 + 基础评测。

---

## 2. 总体技术路线

项目总体路线如下：

```text
实验室安全资料收集
        ↓
资料清洗与结构化整理
        ↓
知识库 CSV 标准化
        ↓
Dify Dataset 导入与索引
        ↓
Dify RAG 问答工作流配置
        ↓
FastAPI 代理与本地展示页面
        ↓
本地安全规则校验与结构化兜底
        ↓
答案生成、引用展示与低置信记录
        ↓
测试集评测与持续优化
```

对应到当前项目文件：

| 技术环节 | 当前文件/目录 |
|---|---|
| 知识库数据 | `knowledge_base_curated.csv` |
| Dify 导入包 | `release_exports/v8.2/knowledge_base_import_ready.csv` |
| 安全规则 | `safety_rules.yaml` |
| Dify 调用 | `web_demo/services/upstream_service.py` |
| 本地检索 | `web_demo/services/kb_service.py` |
| 问答接口 | `web_demo/routers/chat_routes.py` |
| 页面展示 | `web_demo/templates/index.html` |
| 启动脚本 | `scripts/start_dify_rag_local.ps1` |
| 导入脚本 | `scripts/release/import_csv_to_dify_dataset.py` |
| 测试集 | `eval_set_v1.csv` |

---

## 3. 数据与知识库建设路线

### 3.1 数据来源范围

本项目的知识库主要围绕实验室安全典型场景整理，建议覆盖以下类别：

1. 危险化学品基础知识；
2. 设备操作安全要求；
3. 个体防护用品（PPE）要求；
4. 废弃物分类与处置；
5. 应急处置流程；
6. 实验室通风、消防、电气等通用安全要求；
7. 学校或实验室内部安全制度、SOP 和培训材料。

当前已具备：

- 本地知识库：`knowledge_base_curated.csv`；
- Dify 导入包：`release_exports/v8.2/knowledge_base_import_ready.csv`；
- 评测集：`eval_set_v1.csv`。

### 3.2 知识条目结构

知识库采用 CSV 结构化方式维护，核心字段包括：

| 字段 | 说明 |
|---|---|
| `id` | 知识条目唯一编号 |
| `title` | 条目标题 |
| `category` | 大类，如化学、电气、生物等 |
| `subcategory` | 子类，如危化品、设备、应急等 |
| `risk_level` | 风险等级 |
| `hazard_types` | 危险类型 |
| `question` | 典型问题 |
| `answer` | 标准回答 |
| `steps` | 建议步骤 |
| `ppe` | 个体防护要求 |
| `forbidden` | 禁止事项 |
| `emergency` | 应急升级要求 |
| `source_title` | 来源标题 |
| `source_org` | 来源机构 |
| `source_url` | 来源链接 |
| `status` | 条目状态 |
| `tags` | 标签 |

### 3.3 知识库质量控制

知识库建设建议遵循以下流程：

1. 资料收集：收集制度文件、SOP、MSDS、安全手册和公开安全指南；
2. 字段拆分：将长文本拆成问题、回答、步骤、PPE、禁止事项和应急要求；
3. 来源标注：为每条知识保留来源标题、来源机构和来源链接；
4. 风险分级：根据问题场景标注低、中、高、严重风险；
5. 去重校验：检查重复 ID、重复问题和空字段；
6. 人工复核：导入 Dify 前对高风险知识条目进行人工复核；
7. 导入发布：将通过审核的条目导入 Dify Dataset；
8. 持续补强：低置信问题进入补强队列，后续补充或重写知识条目。

---

## 4. Dify RAG 工作流路线

### 4.1 Dify 在本项目中的作用

Dify 主要承担以下角色：

1. 管理实验室安全知识库；
2. 对用户问题进行知识检索；
3. 将检索结果传入大语言模型；
4. 生成面向用户的自然语言回答；
5. 提供应用 API，供本地页面或后端调用。

### 4.2 Dify API 调用流程

当前项目中的 Dify 调用逻辑位于：

`web_demo/services/upstream_service.py`

调用流程：

```text
用户问题
  ↓
/api/chat
  ↓
call_dify_lab(question)
  ↓
POST {DIFY_BASE_URL}/v1/chat-messages
  ↓
Dify 工作流执行知识检索与回答生成
  ↓
返回 SSE 流式响应
  ↓
parse_sse_answer 解析 answer
  ↓
sanitize_llm_output 清洗输出
  ↓
返回前端展示
```

Dify 请求核心参数：

```json
{
  "inputs": {},
  "query": "用户问题",
  "response_mode": "streaming",
  "conversation_id": "",
  "user": "web-demo-lab",
  "auto_generate_name": false
}
```

### 4.3 Dify 配置要求

运行前需要配置：

```env
DIFY_BASE_URL=http://127.0.0.1:8081
DIFY_APP_API_KEY=app-xxxxxxxxxxxxxxxx
DIFY_TIMEOUT=120
```

配置文件：

- 模板：`.env.dify_rag.example`
- 实际运行：`.env.dify_rag`

---

## 5. 本地检索与引用展示路线

虽然主要问答链路走 Dify，但本项目仍保留本地知识库检索，目的有三点：

1. 页面展示引用依据；
2. Dify 不可用时提供结构化兜底；
3. 便于快速检查知识库命中情况。

本地检索入口：

`web_demo/services/kb_service.py`

检索方式：

1. 对用户问题进行文本归一化；
2. 提取关键词和中文 n-gram；
3. 在标题、问题、标签、正文中计算匹配分数；
4. 可选使用 embedding 语义检索；
5. 返回 Top-K 引用条目。

接口：

```http
GET /api/search?q=化学品泄漏&top_k=5
```

返回字段包括：

- `kb_id`
- `title`
- `source_title`
- `source_org`
- `source_url`
- `risk_level`
- `snippet`
- `score`

---

## 6. 安全规则约束路线

实验室安全场景中，高风险问题不能完全依赖大模型自由生成。本项目引入本地规则文件：

`safety_rules.yaml`

规则匹配逻辑：

`web_demo/services/kb_service.py`

主要流程：

```text
用户问题
  ↓
match_rule(question)
  ↓
命中安全规则
  ↓
should_enforce_terminal_rule 判断是否终止
  ↓
若为高风险终止动作，直接返回规则回答
  ↓
否则继续调用 Dify，并在返回中保留风险提示
```

规则动作包括：

| 动作 | 说明 |
|---|---|
| `refuse` | 拒绝危险操作建议 |
| `redirect_emergency` | 引导应急处置 |
| `ask_for_more_info` | 要求补充信息 |
| `safe_answer` | 安全提示后继续回答 |

规则回答生成：

`web_demo/services/answer_service.py`

输出结构包括：

1. 结论；
2. 步骤；
3. 禁止事项；
4. 应急升级；
5. 参考依据。

---

## 7. 结构化兜底路线

当 Dify 未配置、不可达或返回空答案时，本项目不会直接报错给用户，而是启用结构化兜底：

`build_fallback_lab_answer(...)`

兜底回答依据：

1. 本地知识库检索结果；
2. 最高风险等级；
3. 命中的安全规则；
4. 低置信原因。

兜底回答用于保证原型可演示，但在正式申报和验收时应明确：

> 正式主链路是 Dify RAG 工作流，结构化兜底仅用于 Dify 不可用时的安全降级。

---

## 8. 低置信问题补强路线

对于没有命中知识库或命中分数较低的问题，系统会标记为低置信问题。

判断逻辑：

`assess_low_confidence(citations)`

默认阈值：

```env
LOW_CONFIDENCE_TOP_SCORE=3.5
```

低置信问题会记录到：

`artifacts/low_confidence_followups/data_gap_queue.csv`

记录字段包括：

- 问题；
- 问题哈希；
- 决策类型；
- 风险等级；
- 命中规则；
- 低置信原因；
- 引用数量；
- Top 引用条目；
- 建议处理动作。

该机制用于形成后续知识库补强闭环。

---

## 9. 测试评估路线

项目评估分为三个层次。

### 9.1 基础可用性测试

检查：

1. 应用是否能启动；
2. `/health` 是否正常；
3. `/api/meta` 是否返回元信息；
4. `/api/search` 是否能检索知识库；
5. `/api/chat` 是否能返回回答。

### 9.2 Dify 真实链路测试

检查：

1. `.env.dify_rag` 是否配置；
2. Dify Base URL 是否可访问；
3. Dify App Key 是否有效；
4. `/api/chat` 是否返回 `model=dify-workflow`；
5. 回答是否来自 Dify 工作流；
6. 超时和空回答是否有兜底。

### 9.3 问答质量测试

使用：

`eval_set_v1.csv`

建议统计：

| 指标 | 说明 |
|---|---|
| 测试题数 | 本轮测试问题数量 |
| 成功响应数 | 成功返回回答的问题数量 |
| 引用返回率 | 返回 citations 的比例 |
| 高风险合规响应率 | 高风险问题是否拒答或应急引导 |
| 有效回答率 | 人工判定可接受回答比例 |
| 平均响应时间 | 单题平均耗时 |
| P95 响应时间 | 95 分位耗时 |
| 失败样例 | 失败问题和原因 |

---

## 10. 阶段成果路线

本项目建议形成以下成果：

| 成果 | 文件/证据 |
|---|---|
| 实验室安全知识库 | `knowledge_base_curated.csv` |
| Dify 导入数据包 | `release_exports/v8.2/knowledge_base_import_ready.csv` |
| Dify RAG 问答原型 | `web_demo/` |
| 安全规则库 | `safety_rules.yaml` |
| 测试集 | `eval_set_v1.csv` |
| 运行说明 | `docs/ops/部署与运行说明.md` |
| 使用说明 | `docs/ops/用户使用说明.md` |
| 测试报告 | `docs/eval/dify_rag_smoke_test_*.md` |
| 导入报告 | `docs/eval/dify_import_report.md` |
| 申报书正式稿 | `docs/proposal/申报书_基于Dify的实验室安全小助手_标准课题版.docx` |

---

## 11. 技术风险与应对

| 风险 | 表现 | 应对措施 |
|---|---|---|
| Dify 服务不可用 | API 超时或连接失败 | 保留结构化兜底；记录日志；检查 Base URL 和 Key |
| 知识库命中不足 | 引用为空或低分 | 低置信问题入队；补充知识条目 |
| 高风险回答不安全 | 模型可能输出危险建议 | 本地规则前置拦截；高风险问题直接规则回答 |
| 知识条目质量不稳定 | 回答依据不完整 | 人工复核高风险条目；保留来源字段 |
| 响应延迟波动 | Dify 或模型响应慢 | 设置超时；优化 Dify 工作流；减少无关上下文 |
| 申报目标过大 | 现有证据不足 | 将目标调整为阶段性原型目标 |

---

## 12. 本项目不做的内容

为保证第一个项目可控，本项目暂不包含以下内容：

1. 风险评估模块；
2. 开工前检查与阻断；
3. 培训考核；
4. 管理端看板；
5. 事故复盘；
6. 多角色权限系统；
7. 多模态识别；
8. 大规模生产部署；
9. 多实验室长期试点。

这些内容可作为第二个大创优化项目继续推进。

---

## 13. 建议写入申报书的技术路线表述

可直接写入申报书：

> 本课题采用“资料结构化整理—Dify 知识库导入—RAG 工作流配置—安全规则约束—问答测试评估”的技术路线。首先收集实验室安全制度、SOP、MSDS、设备操作规程和应急处置资料，整理为结构化知识条目；其次将通过审核的知识条目导入 Dify Dataset，并配置知识检索与大语言模型回答生成工作流；再次通过 FastAPI 构建本地访问接口和演示页面，实现实验室安全问题输入、Dify 回答调用和知识引用展示；同时引入本地安全规则，对高风险问题进行拒答、应急引导或要求补充信息，降低大模型不当回答风险；最后利用测试集对问答有效性、引用命中和高风险响应进行评估，并将低置信问题沉淀到知识库补强队列中，形成可持续优化的实验室安全问答原型。
