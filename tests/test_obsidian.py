from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vgtree.obsidian import MAX_AUDIT_FILE_BYTES, ObsidianWorkspace


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

    def test_live_audit_rejects_executable_inside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            ObsidianWorkspace().scaffold(vault, "core")
            fake_cli = vault / "obsidian"
            fake_cli.write_text("not executable", encoding="utf-8")

            result = ObsidianWorkspace(cli_path=fake_cli).audit(
                vault, "core", live=True
            )

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.code, "OBSIDIAN_CLI_UNTRUSTED")

    def test_audit_rejects_required_symlink_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "vault"
            outside = root / "outside.md"
            workspace = ObsidianWorkspace()
            workspace.scaffold(vault, "core")
            outside.write_text("outside private bytes", encoding="utf-8")
            (vault / "HOME.md").unlink()
            try:
                (vault / "HOME.md").symlink_to(outside)
            except OSError:
                (vault / "HOME.md").write_text("placeholder", encoding="utf-8")
                with patch("vgtree.obsidian.Path.is_symlink", return_value=True):
                    result = workspace.audit(vault, "core")
            else:
                result = workspace.audit(vault, "core")

            self.assertEqual(result.status, "REVIEW_REQUIRED")
            self.assertIn(
                "PATH_UNSAFE", {item["code"] for item in result.data["findings"]}
            )
            self.assertNotIn("outside private bytes", str(result.as_dict()))

    def test_audit_rejects_oversized_required_file_before_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            workspace = ObsidianWorkspace()
            workspace.scaffold(vault, "core")
            (vault / "HOME.md").write_bytes(b"x" * (MAX_AUDIT_FILE_BYTES + 1))

            result = workspace.audit(vault, "core")

            self.assertEqual(result.status, "REVIEW_REQUIRED")
            self.assertIn(
                "FILE_TOO_LARGE",
                {item["code"] for item in result.data["findings"]},
            )


if __name__ == "__main__":
    unittest.main()
