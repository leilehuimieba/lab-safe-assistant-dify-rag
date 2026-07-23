"""Regression guard: semantic embedding must default to OFF.

The whole project's documented runtime口径 is keyword-search RAG
(.env.dify_rag / docs/ops: ENABLE_EMBEDDING=0). If the code default ever
flips back to ON, any script that does not load .env (quality_gate.py,
pytest) blocks on a ~2GB bge-m3 model download that can hang indefinitely
without raising — which already produced multi-hour orphaned processes once.
These tests lock the default to OFF and keep it opt-in.
"""

from pathlib import Path
import os
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from libs import embedding_utils


class EmbeddingDefaultOffTests(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.get("ENABLE_EMBEDDING")

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("ENABLE_EMBEDDING", None)
        else:
            os.environ["ENABLE_EMBEDDING"] = self._saved

    def test_disabled_when_env_unset(self) -> None:
        os.environ.pop("ENABLE_EMBEDDING", None)
        self.assertFalse(
            embedding_utils._embedding_enabled(),
            "semantic embedding must be OFF by default so scripts that do not "
            "load .env never block on a bge-m3 download",
        )

    def test_disabled_when_env_is_zero(self) -> None:
        os.environ["ENABLE_EMBEDDING"] = "0"
        self.assertFalse(embedding_utils._embedding_enabled())

    def test_enabled_only_when_env_is_one(self) -> None:
        os.environ["ENABLE_EMBEDDING"] = "1"
        self.assertTrue(embedding_utils._embedding_enabled())

    def test_semantic_search_returns_none_by_default(self) -> None:
        """The public entry point must fall back (return None) when unset,
        regardless of whether sentence-transformers is installed."""

        os.environ.pop("ENABLE_EMBEDDING", None)
        result = embedding_utils.semantic_search(
            query="化学品泄漏怎么办",
            entries=[],
            texts=[],
            cache_dir=REPO_ROOT / ".cache" / "embedding",
            kb_file_mtime=0.0,
            top_k=3,
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
