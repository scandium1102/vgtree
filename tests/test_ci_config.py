from __future__ import annotations

import re
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

    def test_all_github_actions_are_pinned_to_full_commit_sha(self) -> None:
        for path in (ROOT / ".github" / "workflows").glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            uses = re.findall(r"uses:\s*([^\s#]+)", text)
            with self.subTest(path=path.name):
                self.assertGreater(len(uses), 0)
                for reference in uses:
                    self.assertRegex(reference, r"^[^@]+@[0-9a-f]{40}$")

    def test_release_separates_read_only_build_from_write_publish(self) -> None:
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("--require-hashes -r requirements/release.txt", text)
        self.assertIn("--no-build-isolation --no-deps -e .", text)
        self.assertIn("needs: build", text)
        self.assertIn("contents: write", text)
        release_block = text.split("\n  release:\n", 1)[1]
        self.assertNotIn("actions/checkout", release_block)
        self.assertNotIn("pip install", release_block)
        self.assertIn("sha256sum -c SHA256SUMS", release_block)

    def test_release_dependency_lock_is_hash_pinned(self) -> None:
        lock = (ROOT / "requirements" / "release.txt").read_text(encoding="utf-8")

        self.assertIn("--hash=sha256:", lock)
        self.assertIn("build==", lock)
        self.assertIn("setuptools==", lock)
        self.assertIn("wheel==", lock)

    def test_publish_job_names_repository_without_git_checkout(self) -> None:
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        release_block = text.split("\n  release:\n", 1)[1]

        self.assertNotIn("actions/checkout", release_block)
        self.assertIn('GH_REPO: ${{ github.repository }}', release_block)


if __name__ == "__main__":
    unittest.main()
