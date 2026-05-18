# 长文档语义切分包报告（原 3000+ 口径已纠偏）
> 口径纠偏（2026-04-29）：本包是把 398 条长文档知识拆成 3164 个检索片段，作用是提升 RAG 检索粒度；不能将其表述为新增 3000+ 条独立外部权威数据。真实外部数据采集已另行生成 `release_exports/v10_external_sources/knowledge_base_external_import_ready.csv`（530 条）。

- source_csv: `D:\newwork\lab-safe-assistant-dify-rag\release_exports\v8.2\knowledge_base_import_ready.csv`
- output_csv: `D:\newwork\lab-safe-assistant-dify-rag\release_exports\v9_original_claim_3000\knowledge_base_import_ready_3000.csv`
- source_rows: `398`
- expanded_rows: `3164`
- original_target_label: `3000+ 条结构化知识库`
- corrected_usage: `检索粒度优化 / chunking experiment，不作为独立新增来源证明`
- method: 将长文档知识按语义句段拆分为可检索知识片段，保留来源、类别、风险等级、标签和问答字段。

## 分类统计

| category | count |
|---|---:|
| biosafety | 394 |
| lab_management | 370 |
| training | 291 |
| 标准 | 290 |
| chemical | 273 |
| 制度 | 205 |
| standard | 170 |
| 设备安全 | 145 |
| 化学 | 138 |
| 通用 | 113 |
| 实验室管理 | 105 |
| 检测方法 | 103 |
| 生物 | 94 |
| 培训 | 88 |
| 实验室设备安全 | 81 |
| equipment | 78 |
| emergency | 45 |
| SDS | 41 |
| radiation | 39 |
| 实验设备 | 31 |
| 电气安全 | 31 |
| 危险源管理 | 14 |
| 专项安全 | 10 |
| 危化品 | 7 |
| 电气 | 6 |
| 辐射 | 2 |

- sha256: `d06dae454f16f78f134a122569da0ce4cacfbcaa3bb5acfe16d24147cb827229`
