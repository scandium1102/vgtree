from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from vgtree.capability import validate_capability_map
from vgtree.receipts import validate_receipt
from vgtree.validation import validate_evidence, validate_state


ROOT = Path(__file__).resolve().parents[1]


class PublicDocumentationTests(unittest.TestCase):
    def test_required_public_surfaces_exist(self) -> None:
        required = (
            "README.md",
            "README.zh-TW.md",
            "LICENSE",
            "SECURITY.md",
            "PRIVACY.md",
            "TERMS.md",
            "SUPPORT.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "docs/architecture.md",
            "docs/uid-modes.md",
            "docs/obsidian.md",
            "docs/migration.md",
            "docs/plugin.md",
            "docs/release-verification-v1.1.0.md",
            "docs/security-review-v1.1.0.md",
            "examples/task.json",
            "examples/evidence.json",
            "examples/workflow-registry.json",
            "examples/capability-map.json",
            "examples/baseline-evidence.json",
            "examples/state-2.1.json",
            "examples/receipt.json",
            "examples/receipt-evidence.json",
        )
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_readmes_cover_install_cli_plugin_and_obsidian(self) -> None:
        for relative in ("README.md", "README.zh-TW.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("pip install git+https://github.com/scandium1102/vgtree.git@v1.1.0", text)
                self.assertIn("vgtree classify", text)
                self.assertIn("vgtree obsidian scaffold", text)
                self.assertIn("six", text.lower() if relative == "README.md" else text)
                self.assertIn("Capability Map", text)
                self.assertIn("Coverage Gate", text)
                self.assertIn("Receipts", text)
                self.assertIn("Context Budget", text)
                self.assertIn("Obsidian", text)

    def test_v11_public_trust_boundaries_are_documented(self) -> None:
        privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8").lower()
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8").lower()
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("no telemetry", privacy)
        self.assertIn("receipt", privacy)
        self.assertIn("structural", security)
        self.assertIn("receipt root", security)
        self.assertIn("## [1.1.0] - 2026-08-21", changelog)

    def test_examples_are_valid_json(self) -> None:
        for path in (ROOT / "examples").glob("*.json"):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    def test_root_schemas_match_packaged_schemas(self) -> None:
        for name in (
            "task.schema.json",
            "state.schema.json",
            "capability-map.schema.json",
            "receipt.schema.json",
        ):
            root_schema = (ROOT / "schemas" / name).read_bytes()
            package_schema = (ROOT / "src" / "vgtree" / "schemas" / name).read_bytes()
            self.assertEqual(root_schema, package_schema, name)

    def test_capability_map_example_is_valid(self) -> None:
        example = json.loads(
            (ROOT / "examples" / "capability-map.json").read_text(encoding="utf-8")
        )
        self.assertTrue(validate_capability_map(example).valid)

    def test_coverage_examples_are_valid(self) -> None:
        baseline = json.loads(
            (ROOT / "examples" / "baseline-evidence.json").read_text(encoding="utf-8")
        )
        state = json.loads(
            (ROOT / "examples" / "state-2.1.json").read_text(encoding="utf-8")
        )
        self.assertTrue(validate_evidence(baseline).valid)
        self.assertTrue(validate_state(state).valid)
        self.assertEqual(state["coverage"]["execution_stage"], "WIDE")

    def test_receipt_examples_are_digest_bound(self) -> None:
        receipt_path = ROOT / "examples" / "receipt.json"
        raw = receipt_path.read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
        evidence = json.loads(
            (ROOT / "examples" / "receipt-evidence.json").read_text(encoding="utf-8")
        )
        self.assertTrue(validate_receipt(receipt).valid)
        self.assertTrue(validate_evidence(evidence).valid)
        self.assertEqual(evidence["digest"], "sha256:" + hashlib.sha256(raw).hexdigest())

    def test_public_text_has_no_private_workspace_markers(self) -> None:
        forbidden = (
            "C:\\" + "Users\\" + "user",
            "Obsidian new" + " second brain",
            "SCANDIAL" + "_SECOND_BRAIN",
            "Sca" + "dio",
            "PRJ-" + "0018",
            "FILE-" + "000091",
        )
        extensions = {".md", ".json", ".yaml", ".yml", ".toml", ".py", ".svg"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in extensions or ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for marker in forbidden:
                with self.subTest(path=str(path.relative_to(ROOT)), marker=marker):
                    self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
