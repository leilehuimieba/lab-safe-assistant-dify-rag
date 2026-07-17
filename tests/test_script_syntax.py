from __future__ import annotations

import py_compile
import subprocess
import sys
import unittest
from pathlib import Path


class ActiveScriptSyntaxTests(unittest.TestCase):
    def test_all_active_python_scripts_compile(self) -> None:
        root = Path(__file__).resolve().parents[1] / "scripts"
        failures: list[str] = []
        for path in sorted(root.rglob("*.py")):
            if "_archive" in path.parts:
                continue
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{path.relative_to(root.parent)}: {exc.msg}")
        self.assertEqual([], failures, "\n".join(failures))

    def test_eval_release_script_can_run_directly(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "run_eval_release_oneclick.py"), "--help"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
