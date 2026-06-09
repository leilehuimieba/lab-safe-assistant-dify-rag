# 验收证据入口

> 当前整理日期：2026-06-09  
> 当前项目：基于 Dify 搭建 RAG 增强的大语言模型实验室安全小助手系统

本目录用于集中放置“当前验收可直接引用”的证据索引和复核记录，避免最新状态分散在历史执行文档、运行产物和截图目录中。

## 当前优先阅读

1. `验收记录_20260609.md`
   - 记录 2026-06-09 本地 Demo、3009 条知识库展示、规则拦截、截图证据、接口性能、Dify 上游恢复、流式问答复核和端到端测试状态。
2. `../design/kb-viz.md`
   - 记录 3000+ 知识库可视化展示的设计口径，以及服务端分页 + 前端虚拟渲染的收口说明。
3. `../proposal/项目完成度与收口计划_20260522.md`
   - 作为项目总体完成度和后续长期证据累计的主口径。
4. `../proposal/验收自查报告_20260522.md`
   - 作为标准课题版验收与高目标验收差异的主口径。

## 截图证据

本轮截图统一放在：

`artifacts/screenshots/acceptance_20260609/`

当前包含：

| 文件 | 说明 |
|---|---|
| `01_chat_home_3009.png` | 首页与右侧 3009 知识库状态 |
| `02_local_search_citations.png` | 本地知识库检索与引用展示 |
| `03_kb_overview_3009.png` | 知识库态势总览，3009 条与 58 个分类 |
| `04_kb_category_drilldown_chemistry.png` | 化学分类下钻视图 |
| `05_kb_entries_paged_virtual_list.png` | 三级明细页，分页加载与虚拟列表 |
| `06_kb_entry_detail_source_trace.png` | 条目详情与来源追溯 |
| `07_rule_engine_blocked_high_risk.png` | 高风险问题由规则引擎拦截 |
| `08_dify_8081_recovered.png` | Dify `8081` Web 端恢复，页面进入 `/apps` |
| `09_demo_dify_workflow_route.png` | Demo 普通问答显示 `Dify 工作流 / Dify 主链路` |
| `10_demo_after_model_route_switch.png` | 模型线路切换后 Demo 首页与系统状态复核 |
| `11_kb_visualization_cockpit_redesign.png` | 知识库态势舱新版视觉，保留分页加载和虚拟列表 |
| `12_kb_entry_detail_drawer_redesign.png` | 知识条目详情抽屉新版视觉与来源追溯展示 |
| `13_e2e_kb_detail_flow.png` | 端到端测试留档：知识库下钻、虚拟列表和详情抽屉 |

## 验收前线路检查

推荐直接执行验收前预检脚本，它会依次恢复 Dify、确认本地 Demo、记录运行快照、验证 Demo 到 Dify 的主链路，并备份 Dify 本地状态：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/prepare_acceptance_precheck.ps1
```

如只想快速检查线路，也可以先恢复 Dify，再检查 Demo 到 Dify 的主链路：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/recover_dify_8081.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify_acceptance_route.ps1
```

其中 `verify_acceptance_route.ps1` 会检查 Demo `/health`、知识库总量与分页明细、Dify `/v1/parameters`，并用普通实验室安全问题验证回答模型为 `dify-workflow`；脚本默认对瞬时超时或 Dify 刚重启后的临时 `502` 进行 `3` 次重试。

Dify 备份由 `scripts/backup_dify_acceptance.ps1` 完成，输出到 `artifacts/backups/dify/`。该目录已加入 `.gitignore`，因为数据库备份可能包含加密后的模型凭据，只作为本地验收证据保存。

补充：`recover_dify_8081.ps1` 默认会在 `docker compose up -d` 后刷新 Dify `nginx` 容器，避免 api/worker 重启后 nginx upstream 缓存旧地址造成临时 `502`。

## 文件整理口径

- `docs/proposal/`：保留申报书、验收自查、完成度、归档清单等正式材料。
- `docs/eval/`：保留历史评测、回归、导入和运行复核记录。
- `docs/ops/`：保留部署、用户使用、长期运行监测方案。
- `docs/design/`：保留系统设计与展示方案。
- `docs/acceptance/`：只放最新验收入口和本轮复核记录。
- `artifacts/screenshots/`：只放可视化截图证据。
- `artifacts/runtime/`：运行时自动产物，作为连续运行证据使用，不建议和代码改动混在一起评审。
