from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from web_demo.routers import meta_routes


class DifyHealthProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        meta_routes._DIFY_HEALTH_CACHE.update(
            {"checked_at": 0.0, "reachable": False, "error": ""}
        )

    @patch.dict(
        os.environ,
        {
            "DIFY_APP_API_KEY": "test-app-key",
            "DIFY_HEALTH_CACHE_SECONDS": "0",
        },
        clear=False,
    )
    @patch("web_demo.routers.meta_routes.requests.get")
    def test_probe_checks_authenticated_parameters_and_closes_response(
        self, mock_get: Mock
    ) -> None:
        response = Mock(status_code=200)
        mock_get.return_value = response

        reachable, error, cached = meta_routes._probe_dify_reachable(
            "http://127.0.0.1:8081/v1"
        )

        self.assertTrue(reachable)
        self.assertEqual("", error)
        self.assertFalse(cached)
        mock_get.assert_called_once_with(
            "http://127.0.0.1:8081/v1/parameters",
            headers={"Authorization": "Bearer test-app-key"},
            timeout=(1, 2),
        )
        response.close.assert_called_once_with()

    @patch.dict(
        os.environ,
        {
            "DIFY_APP_API_KEY": "expired-app-key",
            "DIFY_HEALTH_CACHE_SECONDS": "0",
        },
        clear=False,
    )
    @patch("web_demo.routers.meta_routes.requests.get")
    def test_probe_marks_invalid_app_key_unreachable(self, mock_get: Mock) -> None:
        response = Mock(status_code=401)
        mock_get.return_value = response

        reachable, error, _ = meta_routes._probe_dify_reachable(
            "http://127.0.0.1:8081/v1"
        )

        self.assertFalse(reachable)
        self.assertEqual("dify_http_401", error)
        response.close.assert_called_once_with()

    @patch("web_demo.routers.meta_routes.get_kb_entries", return_value=[{}])
    @patch("web_demo.routers.meta_routes._probe_dify_reachable")
    @patch("web_demo.routers.meta_routes.resolve_dify_api_base")
    def test_health_is_degraded_when_dify_api_is_unavailable(
        self, mock_resolve: Mock, mock_probe: Mock, _mock_kb: Mock
    ) -> None:
        mock_resolve.return_value = "http://127.0.0.1:8081/v1"
        mock_probe.return_value = (False, "dify_http_401", False)

        payload = meta_routes.health()

        self.assertTrue(payload["ok"])
        self.assertEqual("degraded", payload["status"])
        self.assertFalse(payload["dify_reachable"])


if __name__ == "__main__":
    unittest.main()
