# 批量评测报告：accuracy_expansion_round5

> 日期：2026-05-22
> 项目：基于 Dify 的实验室安全小助手

## 总体结果

- 评测题数：24
- HTTP 成功：24/24
- 平均耗时：106ms
- 中位数耗时：102ms
- 最大耗时：212ms
- 决策分布：{'dify_answer': 17, 'rule_blocked': 2, 'need_more_info': 2, 'rule_direct_answer': 1, 'emergency_redirect': 2}

- 模型分布：{'local-fast-path': 17, 'rule-engine': 7}
- 缓存命中：0/24

## 类别分布

- 化学: 15
- 设备: 3
- 通用: 6

## 人工评分

待人工评分后填写。评分标准：
- 3 分（完全正确）：回答准确、引用可靠、步骤完整
- 2 分（基本可用）：回答方向正确，但不够完整或存在轻微冗余
- 1 分（不可用）：回答错误、遗漏关键安全信息或存在安全隐患

人工评分 CSV：`accuracy_expansion_round5_for_review.csv`
