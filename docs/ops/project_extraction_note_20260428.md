# 项目一抽离说明

抽离时间：2026-04-28

## 抽离来源

- 原项目根目录：`D:\newwork\lab-safe-assistant-workspace\lab-safe-assistant-github`
- 申报书模板：`D:\newwork\lab-safe-assistant-workspace\standard_from_doc.docx`

## 抽离目标

建立独立项目：`D:\newwork\lab-safe-assistant-dify-rag`

用于承载第一个项目：

> 基于 Dify 搭建 RAG 增强的大语言模型实验室安全小助手系统

## 已搬迁内容

- Dify 调用链路：`web_demo/services/upstream_service.py`
- 问答路由：`web_demo/routers/chat_routes.py`
- 知识库检索：`web_demo/services/kb_service.py`
- 安全规则回答和低置信队列：`web_demo/services/answer_service.py`
- 最小 Web 页面：`web_demo/templates/index.html`
- 知识库：`knowledge_base_curated.csv`
- 安全规则：`safety_rules.yaml`
- 评测集：`eval_set_v1.csv`
- Dify 导入脚本：`scripts/release/import_csv_to_dify_dataset.py`
- 标准申报书模板：`docs/proposal/standard_from_doc.docx`

## 未搬迁内容

- 风险评估
- 开工前检查
- 培训考核
- 管理看板
- 事故复盘
- 试点闭环材料

这些留在原项目中作为第二个“大创优化版”项目使用。
