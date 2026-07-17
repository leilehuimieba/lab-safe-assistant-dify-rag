from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException

from web_demo.services.auth_service import verify_password


def _request(password: str = "") -> Mock:
    request = Mock()
    request.headers = {"x-password": password} if password else {}
    request.query_params = {}
    return request


class DemoAuthenticationTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=False)
    def test_missing_server_password_disables_protected_endpoints(self) -> None:
        os.environ.pop("DEMO_PASSWORD", None)

        with self.assertRaises(HTTPException) as caught:
            verify_password(_request())

        self.assertEqual(503, caught.exception.status_code)

    @patch.dict(os.environ, {"DEMO_PASSWORD": "correct-password"}, clear=False)
    def test_wrong_password_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            verify_password(_request("wrong-password"))

        self.assertEqual(401, caught.exception.status_code)

    @patch.dict(os.environ, {"DEMO_PASSWORD": "correct-password"}, clear=False)
    def test_correct_password_is_accepted(self) -> None:
        verify_password(_request("correct-password"))


if __name__ == "__main__":
    unittest.main()
