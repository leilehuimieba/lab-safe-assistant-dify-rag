from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _requirements(path: Path) -> set[str]:
    return {
        line.split("==", 1)[0].split(">=", 1)[0].strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


class RuntimeDependencyTests(unittest.TestCase):
    def test_multipart_form_dependency_is_declared_for_all_runtime_installs(self) -> None:
        """FastAPI File/Form routes must import in both root and web-demo installs."""

        for relative_path in ("requirements.txt", "web_demo/requirements.txt"):
            with self.subTest(requirements_file=relative_path):
                requirements = _requirements(REPO_ROOT / relative_path)
                self.assertIn(
                    "python-multipart",
                    requirements,
                    f"{relative_path} must declare python-multipart because the app "
                    "exposes multipart form upload routes",
                )


if __name__ == "__main__":
    unittest.main()
