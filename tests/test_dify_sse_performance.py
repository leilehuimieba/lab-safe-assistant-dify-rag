from scripts.measure_dify_sse_performance import percentile, summarize_samples


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
