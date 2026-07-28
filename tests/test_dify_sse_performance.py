from scripts.measure_dify_sse_performance import (
    evaluate_first_event_target,
    percentile,
    summarize_samples,
)


def test_percentile_uses_linear_interpolation():
    assert percentile([100.0, 200.0, 300.0, 400.0], 0.95) == 385.0


def test_summarize_samples_separates_successes_and_failures():
    summary = summarize_samples(
        [
            {
                "success": True,
                "header_ms": 100.0,
                "first_event_ms": 200.0,
                "first_answer_ms": 300.0,
                "total_ms": 1000.0,
            },
            {
                "success": True,
                "header_ms": 200.0,
                "first_event_ms": 400.0,
                "first_answer_ms": 500.0,
                "total_ms": 2000.0,
            },
            {
                "success": False,
                "header_ms": 900.0,
                "first_event_ms": None,
                "first_answer_ms": None,
                "total_ms": 900.0,
            },
        ]
    )

    assert summary["sample_count"] == 3
    assert summary["success_count"] == 2
    assert summary["failure_count"] == 1
    assert summary["first_event_p50_ms"] == 300.0
    assert summary["total_p95_ms"] == 1950.0


def test_first_event_target_requires_all_samples_and_p95_within_limit():
    passing = evaluate_first_event_target(
        {
            "sample_count": 20,
            "success_count": 20,
            "failure_count": 0,
            "first_event_p95_ms": 1429.2,
        },
        target_ms=3000.0,
    )
    assert passing == {
        "target_ms": 3000.0,
        "measured_p95_ms": 1429.2,
        "all_samples_succeeded": True,
        "passed": True,
    }

    failing = evaluate_first_event_target(
        {
            "sample_count": 20,
            "success_count": 19,
            "failure_count": 1,
            "first_event_p95_ms": 2500.0,
        },
        target_ms=3000.0,
    )
    assert failing["passed"] is False
    assert failing["all_samples_succeeded"] is False
