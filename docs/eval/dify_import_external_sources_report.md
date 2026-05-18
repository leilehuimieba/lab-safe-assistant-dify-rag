# Dify 外部权威来源扩展包导入报告

> 更新时间：2026-04-29  
> 状态：待导入 / 当前 Dify 后台服务未监听 `http://127.0.0.1:8081`

## 1. 导入对象

- CSV：`D:\newwork\lab-safe-assistant-dify-rag\release_exports\v10_external_sources\knowledge_base_external_import_ready.csv`
- 条目数：`1159`
- 来源报告：`D:\newwork\lab-safe-assistant-dify-rag\release_exports\v10_external_sources\import_bundle_report_external.md`
- 来源种子：`D:\newwork\lab-safe-assistant-dify-rag\data_sources\public_lab_safety_sources_v1.csv`
- 原始抓取证据：`D:\newwork\lab-safe-assistant-dify-rag\artifacts\web_ingest_public_20260429`

## 2. 建议 Dataset

- Dataset 名称：`实验室安全知识库-外部权威来源扩展版`
- 建议用途：单独导入并人工审核，不覆盖原 `实验室安全知识库` 398 条主数据集。

## 3. 当前阻塞

本机当前检测结果：

- `http://127.0.0.1:8091` 本地 Web Demo：已恢复运行；
- `http://127.0.0.1:8081` Dify 后台/API：未监听；
- Docker Desktop / Dify Postgres：当前 Docker API 不可用。

因此本轮已完成真实外部数据采集和导入包生成，但尚未能调用 Dify API 创建 Dataset 或导入 1159 条外部条目。

## 4. Dify 恢复后的导入命令

如果已在 Dify 后台新建 Dataset，可执行：

```powershell
python scripts/release/import_csv_to_dify_dataset.py `
  --csv release_exports/v10_external_sources/knowledge_base_external_import_ready.csv `
  --base-url http://127.0.0.1:8081 `
  --dataset-id <外部来源Dataset_ID> `
  --dataset-api-key dataset-FyjRv2vyQcfMyDP4VL5zMI6H `
  --skip-existing `
  --sleep-ms 5 `
  --report-json artifacts/dify_import_external_sources/import_report.json `
  --report-md docs/eval/dify_import_external_sources_report.md
```

如果 Docker/Postgres 恢复，并且需要自动探测已有 Dataset，可用脚本的 `--auto-detect-dataset` 参数。

## 5. 验收口径

本报告用于证明：项目已经开始按原始申报书要求从公开权威来源补充真实数据。它与 3164 条拆分包不同；3164 条仅作为检索粒度优化，不作为新增外部来源证明。
