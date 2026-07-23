"""Regression guard: structured_fallback must preserve a distinguishable reason.

Batch-D 复测（2026-07-23）发现 2 例 `structured_fallback`，但当时的代码把
`call_dify_lab` 抛出的 `HTTPException.detail` 完全丢弃，所有回退都被记成同一句
"upstream unavailable"，且异常路径不给 `upstream_ms` 赋值（停在 0），导致事后
根因排查只能靠 `server_elapsed_ms` 反推失败模式（读超时 vs 上游空返回 vs 5xx）。

这些测试锁定 `_classify_dify_failure` 能把不同失败模式映射成可区分的中文短标签，
从而让下一次回退直接可读、可归类。
"""

from __future__ import annotations

import unittest

from web_demo.routers.chat_routes import _classify_dify_failure


class ClassifyDifyFailureTests(unittest.TestCase):
    def test_read_timeout_maps_to_timeout_label(self) -> None:
        # requests.ReadTimeout 经 call_dify_lab 包成 dify_request_failed: ...timed out...
        self.assertEqual(
            _classify_dify_failure("dify_request_failed: HTTPConnectionPool(...): Read timed out."),
            "上游响应超时",
        )
        self.assertEqual(
            _classify_dify_failure("dify_request_failed: ReadTimeout"),
            "上游响应超时",
        )

    def test_empty_answer_maps_to_no_content_label(self) -> None:
        self.assertEqual(
            _classify_dify_failure("dify_empty_answer: workflow_finished"),
            "上游未返回有效内容",
        )

    def test_http_error_maps_to_upstream_error_label(self) -> None:
        self.assertEqual(
            _classify_dify_failure("dify_http_504: <html>gateway timeout</html>"),
            "上游响应超时",  # 504 文本含 timeout，超时判定优先
        )
        self.assertEqual(
            _classify_dify_failure("dify_http_500: internal error"),
            "上游返回错误",
        )

    def test_connection_failure_maps_to_connection_label(self) -> None:
        self.assertEqual(
            _classify_dify_failure("dify_request_failed: Connection refused"),
            "上游连接失败",
        )

    def test_config_error_maps_to_config_label(self) -> None:
        self.assertEqual(
            _classify_dify_failure("DIFY_APP_API_KEY is missing."),
            "上游配置错误",
        )

    def test_unknown_detail_falls_back_to_generic_label(self) -> None:
        self.assertEqual(_classify_dify_failure("something entirely new"), "上游暂时不可用")
        self.assertEqual(_classify_dify_failure(""), "上游暂时不可用")

    def test_labels_are_never_the_raw_upstream_text(self) -> None:
        """兜底标签必须是稳定短标签，不能把上游原始报文回传给用户。"""
        raw = "dify_http_502: <html><body>nginx boom secret-internal-detail</body></html>"
        label = _classify_dify_failure(raw)
        self.assertNotIn("secret-internal-detail", label)
        self.assertLess(len(label), 20)


if __name__ == "__main__":
    unittest.main()
