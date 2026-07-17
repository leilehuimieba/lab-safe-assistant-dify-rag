from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from scripts import perf_benchmark, run_eval_batch


class EvalScriptAuthenticationTests(unittest.TestCase):
    @patch("scripts.run_eval_batch.requests.post")
    def test_batch_eval_sends_demo_password(self, mock_post: Mock) -> None:
        response = Mock(status_code=401, text="unauthorized")
        mock_post.return_value = response

        run_eval_batch.run_one(
            "http://127.0.0.1:8091",
            "test question",
            5,
            demo_password="local-secret",
        )

        self.assertEqual(
            {"x-password": "local-secret"},
            mock_post.call_args.kwargs["headers"],
        )

    @patch("scripts.perf_benchmark.requests.post")
    def test_benchmark_sends_demo_password(self, mock_post: Mock) -> None:
        response = Mock(status_code=200)
        mock_post.return_value = response

        perf_benchmark.run_one(
            "http://127.0.0.1:8091",
            "test question",
            5,
            demo_password="local-secret",
        )

        self.assertEqual(
            {"x-password": "local-secret"},
            mock_post.call_args.kwargs["headers"],
        )


if __name__ == "__main__":
    unittest.main()
