from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContinuousIntegrationTests(unittest.TestCase):
    def test_ci_runs_tests_and_builds_package(self) -> None:
        text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m build", text)
        self.assertIn("python-version", text)

    def test_release_workflow_is_tag_gated(self) -> None:
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("v*", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("gh release create", text)
        self.assertIn("dist/*", text)


if __name__ == "__main__":
    unittest.main()
