# 用户端完整回答性能实测

> 口径：从发送 `/api/chat` HTTP 请求到收到完整 JSON `answer`；不是 Dify SSE 首事件。
> 终端安全规则可正确地直接拒绝或要求补充信息，不强行套用常规模板。

## 汇总

- 样本：50；HTTP 200：50；完整最终回答：50
- 平均：139.1 ms；P50：140.4 ms；P95：178.8 ms；最大：185.6 ms
- 目标：完整回答 P95 < 3000.0 ms；判定：**通过**
- 路由分布：`{"local-kb-complete": 21, "local-fast-path": 24, "rule-engine": 5}`

原始数据：`artifacts/performance/app_complete_response_20260801_50.csv`
