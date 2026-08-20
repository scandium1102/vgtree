from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vgtree.obsidian import ObsidianWorkspace


class ObsidianScaffoldTests(unittest.TestCase):
    def test_core_scaffold_passes_core_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "vault"
            workspace = ObsidianWorkspace()

            scaffold = workspace.scaffold(destination, "core")
            audit = workspace.audit(destination, "core")

            self.assertEqual(scaffold.status, "PASS", scaffold)
            self.assertEqual(audit.status, "PASS", audit)
            self.assertTrue((destination / "HOME.md").is_file())
            self.assertTrue(
                (destination / "90_System" / "VGTREE" / "PROJECT_REGISTRY.yaml").is_file()
            )

    def test_governed_scaffold_has_uid_hash_and_lineage_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "vault"
            workspace = ObsidianWorkspace()

            scaffold = workspace.scaffold(destination, "governed")
            audit = workspace.audit(destination, "governed")

            self.assertEqual(scaffold.status, "PASS", scaffold)
            self.assertEqual(audit.status, "PASS", audit)
            self.assertTrue(
                (destination / "90_System" / "VGTREE" / "FILE_REGISTRY.yaml").is_file()
            )
            self.assertTrue((destination / "PROVENANCE.md").is_file())
            self.assertTrue((destination / "TRANSACTIONS.md").is_file())

    def test_scaffold_rejects_nonempty_destination_without_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "vault"
            destination.mkdir()
            existing = destination / "keep.md"
            existing.write_text("keep", encoding="utf-8")

            result = ObsidianWorkspace().scaffold(destination, "core")

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.code, "OBSIDIAN_DESTINATION_NOT_EMPTY")
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep")


class ObsidianAuditTests(unittest.TestCase):
    def test_missing_surfaces_are_review_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = ObsidianWorkspace().audit(Path(directory), "core")

            self.assertEqual(result.status, "REVIEW_REQUIRED")
            self.assertEqual(result.code, "OBSIDIAN_AUDIT_FINDINGS")
            self.assertIn("SURFACE_MISSING", {item["code"] for item in result.data["findings"]})

    def test_governed_audit_detects_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "vault"
            workspace = ObsidianWorkspace()
            workspace.scaffold(destination, "governed")
            with (destination / "STATUS.md").open("a", encoding="utf-8") as handle:
                handle.write("\nDrift\n")

            result = workspace.audit(destination, "governed")

            self.assertEqual(result.status, "REVIEW_REQUIRED")
            self.assertIn("HASH_MISMATCH", {item["code"] for item in result.data["findings"]})

    def test_plan_is_read_only_and_lists_missing_operations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            vault.mkdir()
            before = list(vault.rglob("*"))

            result = ObsidianWorkspace().plan(vault, "governed")

            self.assertEqual(result.status, "PASS", result)
            self.assertGreater(len(result.data["operations"]), 0)
            self.assertEqual(list(vault.rglob("*")), before)

    def test_live_audit_is_blocked_when_obsidian_cli_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            ObsidianWorkspace().scaffold(vault, "core")

            result = ObsidianWorkspace(
                cli_path=Path(directory) / "missing-obsidian"
            ).audit(vault, "core", live=True)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.code, "OBSIDIAN_LIVE_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
