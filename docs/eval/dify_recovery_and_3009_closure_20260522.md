# Dify 恢复与 3009 正式导入闭环记录（2026-05-22）

> 项目路径：`D:/newwork/lab-safe-assistant-dify-rag`
> Dify Compose 目录：`D:/newwork/lab-safe-assistant-workspace/lab-safe-assistant-github/local_env/dify/docker`
> 本轮目标：恢复本地 Dify，并完成 `knowledge_base_curated.csv` 当前 `3009` 行主表的正式导入闭环。

## 1. 结论

本轮闭环已经完成，具体包括：

1. Dify `http://127.0.0.1:8081` 已恢复并返回 HTTP `200`；
2. 新正式 Dataset `实验室安全知识库-3009正式版` 已创建，ID 为 `fdd56abd-a89c-44f0-b6e0-02d5a7fd143d`；
3. `knowledge_base_curated.csv` 已成功正式导入 **3009** 条，`failed=0`；
4. 两个 Dify App 已从旧 `3164` chunk 数据集切换到新正式 `3009` Dataset；
5. 本地 Demo `http://127.0.0.1:8091` 已恢复正常，普通问答回到 `dify-workflow`，高风险问题仍由 `rule-engine` 负责；
6. 当前仍需继续等待并留痕的是：**新 Dataset 后台索引完成截图、性能回归和长期运行证据**。

## 2. 恢复动作与关键证据

### 2.1 恢复 Dify

使用旧工作区的 Dify 本地部署目录执行：

```powershell
docker compose -f "D:/newwork/lab-safe-assistant-workspace/lab-safe-assistant-github/local_env/dify/docker/docker-compose.yaml" up -d
```

恢复后确认：

- `http://127.0.0.1:8081` 返回 HTTP `200`；
- `docker compose ps` 显示 `api / web / nginx / worker / db_postgres / redis / weaviate / sandbox / plugin_daemon` 等核心容器均为 `Up`。

### 2.2 正式导入 3009 主表

正式导入命令：

```powershell
D:/Grammar/python/python.exe scripts/release/import_csv_to_dify_dataset.py `
  --csv knowledge_base_curated.csv `
  --base-url http://127.0.0.1:8081 `
  --dataset-id fdd56abd-a89c-44f0-b6e0-02d5a7fd143d `
  --auto-provision-token `
  --db-container docker-db_postgres-1 `
  --db-user postgres `
  --db-name dify `
  --sleep-ms 0 `
  --report-json artifacts/dify_import_3009/import_report.json `
  --report-md docs/eval/dify_import_3009_report.md
```

结果：

- `created=3009`
- `skipped_existing=0`
- `failed=0`
- 正式 Dataset Token：`dataset-VJ26NFBhgKLnOhzIdVk5OEHJ4lrY9lSU`

机器可读导入结果已保存在：

- `artifacts/dify_import_3009/import_report.json`

### 2.3 切换 App 绑定

通过数据库将两个 App 的 `app_dataset_joins` 切换到新正式 Dataset 后，查询结果为：

- `150519ff-b928-44bd-ace0-219245c286bb` → `fdd56abd-a89c-44f0-b6e0-02d5a7fd143d`
- `50bb549d-e14e-44c1-8ec3-dd10258af67f` → `fdd56abd-a89c-44f0-b6e0-02d5a7fd143d`

这意味着当前两个 Dify App 都已经指向 `3009` 正式数据集。

## 3. 运行态复核

### 3.1 本地 Demo 状态

执行 `scripts/status_dify_rag_local.ps1` 后确认：

- 地址：`http://127.0.0.1:8091`
- 进程：`running=True`
- 健康检查：`200 {"status":"ok"}`
- 配置文件：`D:/newwork/lab-safe-assistant-dify-rag/.env.dify_rag`

### 3.2 `/api/meta` 结果

关键字段如下：

- `knowledge_base_rows=3009`
- `knowledge_base_imported=3009`
- `knowledge_base_chunked=3164`
- `knowledge_base_external=1159`
- `dify_base_url=http://127.0.0.1:8081/v1`
- `dify_app_key_configured=true`

说明本地 Demo 已经读取到“3009 本地主表 + 3009 平台导入”的最新口径。

### 3.3 问答抽检

#### 普通问答样本

问题：`进入化学实验室前通常需要佩戴哪些个人防护装备？`

返回关键字段：

- `decision=dify_answer`
- `model=dify-workflow`
- `elapsed_ms=8165`

结论：普通问答已恢复到 Dify 主链路。

#### 高风险问答样本

问题：`实验室发生化学品泄漏应该怎么做？`

返回关键字段：

- `decision=emergency_redirect`
- `model=rule-engine`
- `risk_level=high`
- `elapsed_ms=429`

结论：高风险问题仍由本地规则引擎优先接管，恢复 Dify 后没有破坏安全兜底逻辑。

## 4. 当前索引状态说明

在 2026-05-22 本轮复核时，数据库查询结果为：

- `total=3009`
- `completed=193`
- `other=2816`

这说明：

1. **正式导入已经完成**；
2. 文档索引仍在 Dify 后台异步进行；
3. 当前可以据此宣称“3009 正式导入闭环已完成”，但**不应提前宣称“索引已全部完成”**，除非补齐最终页面截图或后续查询结果。

## 5. 对项目完成度的影响

本轮完成后，项目状态可更新为：

- 按“标准课题版 / 可演示可验收原型”看：约 **92%—95%**；
- 按“版本4立项书全部高目标”看：约 **68%—72%**。

最关键的变化是：

- 原先“Dify 未恢复、3k 数据未正式导入”的最大平台缺口已经补上；
- 剩余主要工作从“恢复平台”转为“性能、索引留痕、长期运行、专家准确率补证”。

## 6. 还需要人工操作吗？

**当前没有必须立即人工完成的步骤。**

只有在下面两种场景下，建议人工配合：

1. **需要答辩/验收截图**：
   - 登录 `http://127.0.0.1:8081/signin`
   - 打开 Dataset `实验室安全知识库-3009正式版`
   - 截图文档总数与索引完成状态
2. **需要界面确认展示效果**：
   - 在 Dify UI 中查看 App 是否已关联到正式 Dataset
   - 视需要补 App 页面截图

也就是说：

- **恢复与正式导入闭环本身已自动完成**；
- **人工主要只在“截图留痕”这一步才需要介入**。
