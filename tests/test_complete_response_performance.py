from __future__ import annotations


def test_complete_response_target_requires_every_final_answer_and_strict_p95():
    from scripts.measure_complete_response_performance import evaluate_complete_response_target

    passing = [
        {"http_status": 200, "elapsed_ms": value, "answer_nonempty": True}
        for value in [90, 120, 180, 400, 2950]
    ]
    failing = [*passing[:-1], {"http_status": 200, "elapsed_ms": 3000, "answer_nonempty": True}]
    incomplete = [*passing[:-1], {"http_status": 200, "elapsed_ms": 200, "answer_nonempty": False}]

    assert evaluate_complete_response_target(passing, target_ms=3000)["passed"] is True
    assert evaluate_complete_response_target(failing, target_ms=3000)["passed"] is False
    assert evaluate_complete_response_target(incomplete, target_ms=3000)["passed"] is False


def test_complete_response_accepts_terminal_rules_without_forcing_normal_template():
    from scripts.measure_complete_response_performance import is_complete_final_answer

    assert is_complete_final_answer("请补充化学品名称后再判断。", "need_more_info") is True
    assert is_complete_final_answer("结论:\n按 SOP 操作。\n\n步骤:\n1. 核对。\n\n禁止事项:\n- 禁止冒险。", "local_complete_answer") is True
    assert is_complete_final_answer("", "local_complete_answer") is False
