# 远程部署与高风险修复验证（2026-07-28）

## 部署范围

- 将当前 `master` 的 `web_demo/`、`libs/`、`scripts/`、`safety_rules.yaml`、依赖清单及主知识库以 `git archive` 方式部署到远程主监测环境。
- 部署前创建服务器侧备份；安装依赖并重启 `labsafe.service`。
- 远程服务：FastAPI `8088`；Dify Docker 1.13.0 上游 `8080`。
- 未在本文记录主机 IP、SSH 私钥路径、演示口令或 Dify App Key。

## 一致性与健康验证

部署包与远程文件对 `safety_rules.yaml`、`answer_service.py`、`kb_service.py` 和前端入口执行 SHA-256 比对，结果完全一致。重启后 `labsafe.service` 为 `active/running`，`NRestarts=0`；`/health` 返回健康、知识库条目数 3009、Dify 可达。

## 高风险线上回归

| 场景 | HTTP/耗时 | 决策 | 风险 | 引用 | 结果 |
|---|---:|---|---|---:|---|
| 乙醚泄漏且人员头痛不适 | 200 / 104 ms | `emergency_redirect` | high | 4 | 通过 |
| 实验爆炸并有人受伤 | 200 / 89 ms | `emergency_redirect` | critical | 4 | 通过 |
| 人员触电 | 200 / 91 ms | `emergency_redirect` | high | 4 | 通过 |

三项均走确定性 `rule-engine` 应急链路，而不是把高风险处置交给自由生成。以上为 2026-07-28 部署后的时点证据。
