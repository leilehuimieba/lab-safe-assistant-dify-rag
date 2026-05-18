# Dify Dataset Import Report

- generated_at: `2026-04-28T17:28:11+08:00`
- csv_path: `D:\newwork\lab-safe-assistant-dify-rag\release_exports\v8.2\knowledge_base_import_ready.csv`
- base_url: `http://127.0.0.1:8081`
- dataset_id: `abdb8a2b-1e56-457a-b55c-c50c76a63eff`
- created: `398`
- skipped_existing: `0`
- failed: `0`
- batches_count: `398`

## Indexing Status Snapshot

导入完成后已查询 Dify 数据库中的文档索引状态：

| 状态 | 数量 |
|---|---:|
| completed | 158 |
| splitting | 1 |
| waiting | 239 |
| total | 398 |

说明：`created=398`、`failed=0` 表示 398 条文档已成功写入 Dify Dataset；索引任务由 Dify worker 后台继续处理，刚导入完成时部分文档处于 `waiting` / `splitting` 属于正常异步索引状态。

## Evidence

- Dataset name: `实验室安全知识库`
- Dataset id: `abdb8a2b-1e56-457a-b55c-c50c76a63eff`
- Import CSV: `release_exports/v8.2/knowledge_base_import_ready.csv`
- JSON report: `artifacts/dify_import/import_report.json`
