from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from scripts.record_runtime_snapshot import fetch_json


class RuntimeSnapshotTests(unittest.TestCase):
    @patch("scripts.record_runtime_snapshot.requests.get")
    def test_fetch_json_authenticates_and_closes_response(self, mock_get: Mock) -> None:
        response = Mock(status_code=200, text="")
        response.json.return_value = {"ok": True}
        mock_get.return_value = response

        status, payload, error = fetch_json(
            "http://127.0.0.1:8091/api/meta",
            5,
            demo_password="local-secret",
        )

        self.assertEqual(200, status)
        self.assertEqual({"ok": True}, payload)
        self.assertEqual("", error)
        mock_get.assert_called_once_with(
            "http://127.0.0.1:8091/api/meta",
            headers={"x-password": "local-secret"},
            timeout=(8, 5),
        )
        response.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
