from __future__ import annotations

import py_compile
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


if __name__ == "__main__":
    unittest.main()
