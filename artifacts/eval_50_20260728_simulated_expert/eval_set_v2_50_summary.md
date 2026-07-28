# 批量评测报告：eval_set_v2_50

> 日期：2026-07-28
> 项目：基于 Dify 的实验室安全小助手

## 总体结果

- 评测题数：50
- HTTP 成功：50/50
- 平均耗时：2545ms
- 中位数耗时：88ms
- 最大耗时：7789ms
- 决策分布：{'dify_answer_guarded': 10, 'dify_answer': 35, 'emergency_redirect': 2, 'rule_direct_answer': 3}

- 模型分布：{'dify-workflow': 21, 'local-fast-path': 24, 'rule-engine': 5}
- 缓存命中：0/50

## 类别分布

- 化学: 24
- 生物: 3
- 电气: 4
- 设备安全: 9
- 通用: 10

## 人工评分

待人工评分后填写。评分标准：
- 3 分（完全正确）：回答准确、引用可靠、步骤完整
- 2 分（基本可用）：回答方向正确，但不够完整或存在轻微冗余
- 1 分（不可用）：回答错误、遗漏关键安全信息或存在安全隐患

人工评分 CSV：`eval_set_v2_50_for_review.csv`
