from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "vgtree"


class PluginManifestTests(unittest.TestCase):
    def test_skills_only_manifest_is_complete(self) -> None:
        manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["name"], "vgtree")
        self.assertEqual(manifest["version"], "1.1.0")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("apps", manifest)
        self.assertNotIn("hooks", manifest)
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["interface"]["brandColor"], "#6D5DFB")
        self.assertTrue(manifest["interface"]["privacyPolicyURL"].startswith("https://"))
        self.assertTrue(manifest["interface"]["termsOfServiceURL"].startswith("https://"))

    def test_manifest_assets_and_six_skills_exist(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        interface = manifest["interface"]
        for field in ("composerIcon", "logo", "logoDark"):
            self.assertTrue((PLUGIN_ROOT / interface[field]).is_file(), field)

        expected = {
            "using-vgtree",
            "planning-tree-work",
            "executing-tree-work",
            "verifying-tree-work",
            "governing-knowledge-architecture",
            "building-obsidian-workspaces",
        }
        actual = {
            path.parent.name for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(actual, expected)

    def test_repository_marketplace_points_to_plugin(self) -> None:
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(marketplace["name"], "vgtree")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "vgtree")
        self.assertEqual(entry["source"]["path"], "./plugins/vgtree")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")


if __name__ == "__main__":
    unittest.main()
