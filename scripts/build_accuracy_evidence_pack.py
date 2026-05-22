#!/usr/bin/env python3
"""构建“99%准确率证据补强”所需的评审骨架。

输出：
1. accuracy_evidence_pack_v1.csv
   - 合并已有 50 题人工评分结果与最新 30 题申报书对齐回归结果
2. accuracy_priority_queue_v1.csv
   - 自动筛出优先复评队列（历史 2 分题 + 高风险/规则链题）
3. accuracy_evidence_pack_summary.md
   - 给出当前已有证据、待补证据和下一步人工动作
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build accuracy evidence pack")
    parser.add_argument(
        "--eval50",
        default=str(REPO_ROOT / "artifacts" / "eval_50" / "eval_50_for_review.csv"),
        help="Path to the existing 50-question human-scored CSV",
    )
    parser.add_argument(
        "--alignment",
        default=str(REPO_ROOT / "artifacts" / "eval" / "alignment_v2_round6" / "申报书对齐回归集_v2_for_review.csv"),
        help="Path to the latest alignment review CSV",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "artifacts" / "accuracy"),
        help="Directory for generated accuracy evidence artifacts",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize_review_row(
    row: dict[str, str],
    *,
    source_run: str,
    source_type: str,
    index: int,
) -> dict[str, str]:
    human_score = (row.get("human_score") or "").strip()
    decision = (row.get("decision") or "").strip()
    model = (row.get("model") or "").strip()
    risk_text = (row.get("risk_level_expected") or row.get("risk_level") or "").strip()

    review_status = "scored" if human_score else "pending_review"
    priority = "P2"
    if human_score == "2":
        priority = "P0"
    elif decision in {"rule_blocked", "emergency_redirect", "need_more_info", "rule_direct_answer"}:
        priority = "P1"
    elif model == "rule-engine":
        priority = "P1"

    return {
        "pack_id": f"ACC-{index:04d}",
        "source_run": source_run,
        "source_type": source_type,
        "eval_id": (row.get("eval_id") or "").strip(),
        "category": (row.get("category") or "").strip(),
        "subcategory": (row.get("subcategory") or "").strip(),
        "question": (row.get("question") or "").strip(),
        "answer": (row.get("answer") or "").strip(),
        "decision": decision,
        "model": model,
        "elapsed_ms": (row.get("elapsed_ms") or "").strip(),
        "expected_lane": (row.get("expected_lane") or "").strip(),
        "expected_action": (row.get("expected_action") or "").strip(),
        "expected_keywords": (row.get("expected_keywords") or "").strip(),
        "risk_level": risk_text,
        "conversation_group": (row.get("conversation_group") or "").strip(),
        "turn_no": (row.get("turn_no") or "").strip(),
        "citation_0_title": (row.get("citation_0_title") or "").strip(),
        "citation_1_title": (row.get("citation_1_title") or "").strip(),
        "citation_2_title": (row.get("citation_2_title") or "").strip(),
        "human_score": human_score,
        "human_notes": (row.get("human_notes") or "").strip(),
        "review_status": review_status,
        "priority": priority,
        "expert_score": "",
        "expert_notes": "",
        "final_score": human_score,
        "final_notes": (row.get("human_notes") or "").strip(),
    }


def build_summary(rows: list[dict[str, str]], eval50_count: int, alignment_count: int) -> str:
    source_counter = Counter(row["source_run"] for row in rows)
    review_counter = Counter(row["review_status"] for row in rows)
    priority_counter = Counter(row["priority"] for row in rows)
    scored_rows = [row for row in rows if row["review_status"] == "scored" and row["human_score"].isdigit()]

    score_counter: Counter[str] = Counter()
    category_scores: dict[str, list[int]] = defaultdict(list)
    for row in scored_rows:
        score = int(row["human_score"])
        score_counter[str(score)] += 1
        category_scores[row["category"] or "未分类"].append(score)

    total_scored = sum(score_counter.values())
    full_correct_rate = (score_counter["3"] / total_scored * 100) if total_scored else 0.0
    effective_rate = ((score_counter["3"] + score_counter["2"]) / total_scored * 100) if total_scored else 0.0

    lines = [
        "# 99%准确率证据包汇总（v1）",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 50题已评分来源：`artifacts/eval_50/eval_50_for_review.csv`（{eval50_count} 条）",
        f"> 对齐回归来源：`artifacts/eval/alignment_v2_round6/申报书对齐回归集_v2_for_review.csv`（{alignment_count} 条）",
        "",
        "## 1. 当前证据池规模",
        "",
        f"- 合并总条数：`{len(rows)}`",
        f"- 已有人工评分：`{review_counter.get('scored', 0)}`",
        f"- 待人工/专家补评：`{review_counter.get('pending_review', 0)}`",
        f"- 来源分布：`{dict(source_counter)}`",
        "",
        "## 2. 当前已有评分基线",
        "",
        f"- 已评分样本数：`{total_scored}`",
        f"- 有效回答率（≥2分）：`{effective_rate:.1f}%`",
        f"- 完全正确率（3分）：`{full_correct_rate:.1f}%`",
        f"- 分数分布：`{dict(score_counter)}`",
        "",
        "## 3. 优先复评队列",
        "",
        f"- `P0`：`{priority_counter.get('P0', 0)}` 条（历史 2 分题，优先补强）",
        f"- `P1`：`{priority_counter.get('P1', 0)}` 条（高风险/规则链/多轮关键题）",
        f"- `P2`：`{priority_counter.get('P2', 0)}` 条（其余标准题）",
        "",
        "## 4. 已评分类别均分",
        "",
    ]

    for category, scores in sorted(category_scores.items()):
        avg = sum(scores) / len(scores)
        lines.append(f"- {category}: {avg:.2f}（样本 {len(scores)}）")

    lines.extend(
        [
            "",
            "## 5. 下一步人工动作",
            "",
            "1. 先处理 `accuracy_priority_queue_v1.csv` 中的 `P0` 条目，逐条补齐知识与回答质量；",
            "2. 再对 `P1` 条目做专家复评，形成“高风险题准确率专项证据”；",
            "3. 每完成一轮复评，都回写 `expert_score / expert_notes / final_score`；",
            "4. 当扩样后 `final_score=3` 的比例稳定接近 `99%`，再更新申报书高目标口径。",
            "",
            "## 6. 注意",
            "",
            "- 当前这份包是“证据骨架”，不是对 `99%` 准确率的最终宣称；",
            "- 在没有扩样人工/专家评分完成前，仍只能说“已建立准确率补强证据闭环”。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    eval50_path = Path(args.eval50).resolve()
    alignment_path = Path(args.alignment).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not eval50_path.exists():
        raise SystemExit(f"Missing eval50 file: {eval50_path}")
    if not alignment_path.exists():
        raise SystemExit(f"Missing alignment file: {alignment_path}")

    eval50_rows = read_csv(eval50_path)
    alignment_rows = read_csv(alignment_path)

    combined: list[dict[str, str]] = []
    idx = 1
    for row in eval50_rows:
        combined.append(
            normalize_review_row(
                row,
                source_run="eval_50_human_scored",
                source_type="historical_scored",
                index=idx,
            )
        )
        idx += 1
    for row in alignment_rows:
        combined.append(
            normalize_review_row(
                row,
                source_run="alignment_v2_round6",
                source_type="proposal_alignment_round2",
                index=idx,
            )
        )
        idx += 1

    pack_headers = list(combined[0].keys()) if combined else []
    pack_path = out_dir / "accuracy_evidence_pack_v1.csv"
    with pack_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pack_headers)
        writer.writeheader()
        writer.writerows(combined)

    priority_rows = [row for row in combined if row["priority"] in {"P0", "P1"}]
    priority_rows.sort(key=lambda row: (row["priority"], row["source_run"], row["eval_id"]))
    priority_path = out_dir / "accuracy_priority_queue_v1.csv"
    with priority_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pack_headers)
        writer.writeheader()
        writer.writerows(priority_rows)

    summary_path = out_dir / "accuracy_evidence_pack_summary.md"
    summary_path.write_text(
        build_summary(combined, len(eval50_rows), len(alignment_rows)),
        encoding="utf-8",
    )

    print(f"[OK] accuracy pack: {pack_path}")
    print(f"[OK] priority queue: {priority_path}")
    print(f"[OK] summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
