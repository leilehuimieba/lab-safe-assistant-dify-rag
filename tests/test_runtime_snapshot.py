"""运行态快照采集脚本的回归测试。

2026-08-09 排查发现：工作站上常驻的代理客户端（mihomo，监听 127.0.0.1:7897）在
系统代理开启且 ProxyOverride 未包含回环地址时，会接管对 127.0.0.1 的请求并返回
502，使快照把"本地演示服务未启动"记录成"服务返回 502"，两种完全不同的状态被
混为一谈。因此对回环地址必须绕过环境变量与系统代理设置直连。
"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from scripts.record_runtime_snapshot import fetch_json, is_loopback_url


class IsLoopbackUrlTests(unittest.TestCase):
    def test_loopback_hosts_are_recognised(self) -> None:
        for url in (
            "http://127.0.0.1:8091/health",
            "http://localhost:8088/api/meta",
            "http://LOCALHOST:8088/api/meta",
            "http://[::1]:8091/health",
        ):
            with self.subTest(url=url):
                self.assertTrue(is_loopback_url(url))

    def test_remote_hosts_are_not_loopback(self) -> None:
        for url in (
            "http://example.com/health",
            "https://127.0.0.1.example.com/health",
            "http://10.0.0.5:8088/health",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_loopback_url(url))


class FetchJsonTests(unittest.TestCase):
    def _session(self, mock_session_cls: Mock) -> Mock:
        session = mock_session_cls.return_value
        # requests.Session 的默认值，测试里显式还原，便于断言是否被改写。
        session.trust_env = True
        response = Mock(status_code=200, text="")
        response.json.return_value = {"ok": True}
        session.get.return_value = response
        return session

    @patch("scripts.record_runtime_snapshot.requests.Session")
    def test_fetch_json_authenticates_and_closes_response(self, mock_session_cls: Mock) -> None:
        session = self._session(mock_session_cls)

        status, payload, error = fetch_json(
            "http://127.0.0.1:8091/api/meta",
            5,
            demo_password="local-secret",
        )

        self.assertEqual(200, status)
        self.assertEqual({"ok": True}, payload)
        self.assertEqual("", error)
        session.get.assert_called_once_with(
            "http://127.0.0.1:8091/api/meta",
            headers={"x-password": "local-secret"},
            timeout=(8, 5),
        )
        session.get.return_value.close.assert_called_once_with()
        session.close.assert_called_once_with()

    @patch("scripts.record_runtime_snapshot.requests.Session")
    def test_loopback_request_bypasses_proxy(self, mock_session_cls: Mock) -> None:
        session = self._session(mock_session_cls)

        fetch_json("http://127.0.0.1:8091/health", 5)

        self.assertFalse(session.trust_env)

    @patch("scripts.record_runtime_snapshot.requests.Session")
    def test_remote_request_keeps_environment_proxy_settings(self, mock_session_cls: Mock) -> None:
        session = self._session(mock_session_cls)

        fetch_json("http://example.com/health", 5)

        self.assertTrue(session.trust_env)

    @patch("scripts.record_runtime_snapshot.requests.Session")
    def test_transport_error_is_reported_without_raising(self, mock_session_cls: Mock) -> None:
        session = self._session(mock_session_cls)
        session.get.side_effect = RuntimeError("connection refused")

        status, payload, error = fetch_json("http://127.0.0.1:8091/health", 5)

        self.assertEqual(0, status)
        self.assertEqual({}, payload)
        self.assertIn("connection refused", error)
        session.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
