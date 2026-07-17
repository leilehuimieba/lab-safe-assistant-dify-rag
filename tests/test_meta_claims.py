from __future__ import annotations

import unittest
from unittest.mock import patch

from web_demo.services.meta_service import get_demo_meta


class DemoClaimTests(unittest.TestCase):
    @patch("web_demo.services.meta_service.get_kb_entries", return_value=[])
    def test_meta_does_not_claim_unverified_acceptance_or_stability(self, _mock_kb) -> None:
        meta = get_demo_meta()
        combined = " ".join(
            [meta.acceptance_status, meta.formal_eval_score, meta.stability_status]
        )

        self.assertNotIn("20/20", combined)
        self.assertNotIn("3/3 PASS", combined)
        self.assertNotIn("project-1-extracted", combined)
        self.assertIn("专家复核", meta.formal_eval_score)
        self.assertIn("2026-07-01", meta.stability_status)


if __name__ == "__main__":
    unittest.main()
