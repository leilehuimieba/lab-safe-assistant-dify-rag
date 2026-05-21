#!/usr/bin/env python3
"""生成人工抽检样本清单。"""
import csv
import random
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
SAMPLE_FILE = REPO_ROOT / "audit_sample.csv"
GUIDE_FILE = REPO_ROOT / "AUDIT_GUIDE.md"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "audit_id", "kb_id", "title", "category", "subcategory",
    "risk_level", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency",
    "source_title", "source_org",
    # 审核列
    "q1_question_quality", "q2_answer_quality", "q3_category_correct",
    "q4_risk_level", "q5_safety_elements", "q6_source_traceable",
    "total_score", "audit_result", "audit_comment", "corrected"
]

AUDIT_QUESTIONS = {
    "q1_question_quality": "问题(Q)是否通顺、切题、易被用户理解？(0-5)",
    "q2_answer_quality": "回答(A)是否准确、完整、可操作？(0-5)",
    "q3_category_correct": "分类(category/subcategory)是否正确？(0-5)",
    "q4_risk_level": "风险等级(risk_level)是否与内容匹配？(0-5)",
    "q5_safety_elements": "PPE/禁止事项/处置/急救/应急是否完整合理？(0-5)",
    "q6_source_traceable": "来源(source)是否可追溯、可信？(0-5)",
}


def build_guide():
    lines = [
        "# 实验室安全知识库人工抽检指南",
        "",
        f"**生成时间**: {TODAY}",
        "",
        "## 一、抽检样本",
        "",
        f"已生成文件: `{SAMPLE_FILE.name}`",
        "",
        "抽样策略: 按来源批次分层随机抽样，每批次抽取约12条（10%），总计约96条。",
        "",
        "## 二、审核维度与评分标准",
        "",
    ]
    for key, desc in AUDIT_QUESTIONS.items():
        lines.append(f"- **{key}**: {desc}")
    lines.extend([
        "",
        "## 三、评分判定",
        "",
        "| 总分 | 判定 | 操作 |",
        "|------|------|------|",
        "| 26-30 | 优秀 | 直接通过，status改为 `reviewed` |",
        "| 21-25 | 良好 | 小修后通过，status改为 `reviewed` |",
        "| 16-20 | 一般 | 需修改内容，修改后重新抽检 |",
        "| 0-15 | 不合格 | 删除或重写 |",
        "",
        "## 四、审核操作步骤",
        "",
        "1. **打开样本**: 用 Excel / WPS / 其他表格工具打开 `audit_sample.csv`",
        "2. **逐条审核**: 阅读每条记录的 question/answer/steps/ppe 等字段",
        "3. **填写评分**: 在 q1-q6 列填写 0-5 分",
        "4. **计算总分**: total_score = q1 + q2 + q3 + q4 + q5 + q6",
        "5. **填写结论**: audit_result 填写: `pass` / `pass_after_fix` / `needs_revision` / `reject`",
        "6. **填写备注**: audit_comment 填写具体修改意见",
        "7. **标记修正状态**: corrected 填写 `yes` / `no`",
        "",
        "## 五、如何修正知识库",
        "",
        "### 方式A: 直接编辑CSV（少量修改）",
        "",
        "1. 用Excel或文本编辑器打开 `knowledge_base_curated.csv`",
        "2. 搜索对应的 `kb_id`（如 `KB-NEW-0001`）",
        "3. 修改需要调整的字段",
        "4. 将 `status` 列从 `draft` 改为 `reviewed`",
        "5. 将 `reviewer` 列改为审核人姓名",
        "6. 将 `last_updated` 列改为今天日期",
        "7. 保存（保持UTF-8编码，CSV格式）",
        "",
        "### 方式B: 使用修正脚本（批量修改）",
        "",
        "完成审核后，运行以下命令批量更新已通过的数据：",
        "```bash",
        "python scripts/batch_update_status.py audit_sample.csv",
        "```",
        "",
        "## 六、常见问题和处理建议",
        "",
        "| 问题类型 | 示例 | 处理建议 |",
        "|----------|------|----------|",
        "| 问题不通顺 | `关于GC载气钢瓶安全操作规范的安全操作规程是什么？` | 简化为 `GC载气钢瓶有哪些安全操作要求？` |",
        "| 回答太笼统 | 只有措施列表，缺少核心结论 | 在开头加一句总结性回答 |",
        "| 分类错误 | 辐射安全条目被分到`物理` | 改为 `辐射` |",
        "| 风险等级偏高/低 | 普通培训条目risk_level=5 | 根据实际危害调整为1-2 |",
        "| PPE缺失 | 辐射操作没有剂量计 | 补充 `个人剂量计；防护手套；实验服` |",
        "| 来源模糊 | `University Manual` | 补充具体大学和手册名称 |",
        "",
        "## 七、审核完成标准",
        "",
        "- 抽检样本中 `pass` + `pass_after_fix` 比例 ≥ 80%",
        "- 无 `reject` 条目，或 reject 条目已删除",
        "- 所有需要修改的条目已完成修正并重新验证",
        "",
    ])
    return "\n".join(lines)


def main():
    if not KB_FILE.exists():
        print(f"ERROR: {KB_FILE} not found")
        return 1

    with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    new_rows = [r for r in rows if r.get("id", "").startswith("KB-NEW")]
    print(f"新增数据总数: {len(new_rows)}")

    # 按批次分组
    batches = {}
    for r in new_rows:
        batch = r.get("tags", "").split(";")[0] if r.get("tags") else "unknown"
        batches.setdefault(batch, []).append(r)

    # 分层抽样：每批抽 min(12, 总数) 条
    random.seed(42)
    sampled = []
    for batch, items in sorted(batches.items()):
        n = min(12, max(5, len(items) // 10 + 5))
        chosen = random.sample(items, min(n, len(items)))
        print(f"  {batch}: 总数{len(items)}, 抽样{n}, 实际抽{len(chosen)}")
        for r in chosen:
            sampled.append(r)

    print(f"\n抽检样本总数: {len(sampled)}")

    # 写入样本CSV
    with SAMPLE_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for idx, r in enumerate(sampled, 1):
            out = {
                "audit_id": f"AUDIT-{idx:03d}",
                "kb_id": r.get("id", ""),
                "title": r.get("title", ""),
                "category": r.get("category", ""),
                "subcategory": r.get("subcategory", ""),
                "risk_level": r.get("risk_level", ""),
                "question": r.get("question", ""),
                "answer": r.get("answer", ""),
                "steps": r.get("steps", ""),
                "ppe": r.get("ppe", ""),
                "forbidden": r.get("forbidden", ""),
                "disposal": r.get("disposal", ""),
                "first_aid": r.get("first_aid", ""),
                "emergency": r.get("emergency", ""),
                "source_title": r.get("source_title", ""),
                "source_org": r.get("source_org", ""),
                "q1_question_quality": "",
                "q2_answer_quality": "",
                "q3_category_correct": "",
                "q4_risk_level": "",
                "q5_safety_elements": "",
                "q6_source_traceable": "",
                "total_score": "",
                "audit_result": "",
                "audit_comment": "",
                "corrected": "",
            }
            writer.writerow(out)

    # 写入指南
    with GUIDE_FILE.open("w", encoding="utf-8") as f:
        f.write(build_guide())

    print(f"\n样本文件: {SAMPLE_FILE}")
    print(f"指南文件: {GUIDE_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
