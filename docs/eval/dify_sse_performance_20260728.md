# Dify SSE 性能实测

> 生成时间：2026-07-28T17:54:18+08:00
> Dify 地址：`http://127.0.0.1:8080`
> 口径：header=HTTP 响应头；first_event=首个 SSE data 事件；first_answer=首个回答事件；total=完整流结束。
> App Key 仅从环境变量读取，未写入报告或 CSV。

## 汇总

- 样本：50
- 成功：50
- 失败：0
- 预热请求（不计入样本）：2

| 指标 | 平均 | P50 | P95 | 最大 |
|---|---:|---:|---:|---:|
| HTTP 响应头 | 23.9 ms | 19.5 ms | 45.3 ms | 77.4 ms |
| 首个 SSE 事件 | 1246.3 ms | 1124.7 ms | 2135.8 ms | 2487.3 ms |
| 首个回答事件 | 1699.5 ms | 1679.6 ms | 2545.1 ms | 3108.3 ms |
| 完整流 | 5426.6 ms | 5363.4 ms | 6505.9 ms | 6941.2 ms |

## 验收判定

- 首个 SSE 事件 P95 目标：≤ 3000.0 ms
- 实测：2135.8 ms
- 全部正式样本成功：是
- 判定：**通过**

## 结论边界

- 首事件/首字节与完整回答耗时是不同指标，不得互相替代。
- 本次采用 2 次预热 + 50 个正式样本，正式样本全部成功；原始逐题 CSV 已随仓库保留，可复算 P50/P95/最大值。
- 完整回答耗时受模型、网络、工作流和输出长度共同影响。

原始数据：`artifacts/performance/dify_sse_20260728_50.csv`

复测命令（在部署服务器读取密钥环境变量，不把 App Key 写入命令或报告）：

```bash
python scripts/measure_dify_sse_performance.py \
  --base-url http://127.0.0.1:8080 \
  --warmup 2 \
  --limit 50 \
  --max-first-event-p95-ms 3000 \
  --output-csv artifacts/performance/dify_sse_20260728_50.csv \
  --report-md docs/eval/dify_sse_performance_20260728.md
```
