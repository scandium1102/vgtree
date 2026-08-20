import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"


class OpenAISubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.listing = json.loads(
            (SUBMISSION / "openai-listing-v1.1.0.json").read_text(encoding="utf-8")
        )
        cls.cases = json.loads(
            (SUBMISSION / "openai-test-cases-v1.1.0.json").read_text(encoding="utf-8")
        )

    def test_listing_matches_approved_public_contract(self) -> None:
        listing = self.listing
        self.assertEqual("skills-only", listing["submission_type"])
        self.assertEqual("VGTREE", listing["name"])
        self.assertEqual("Productivity", listing["category"])
        self.assertEqual("Branch complex work into verifiable outcomes.", listing["short_description"])
        self.assertEqual("https://scandium1102.github.io/vgtree/", listing["website"])
        self.assertEqual("https://github.com/scandium1102/vgtree/issues", listing["support"])
        self.assertEqual("https://scandium1102.github.io/vgtree/privacy/", listing["privacy"])
        self.assertEqual("https://scandium1102.github.io/vgtree/terms/", listing["terms"])
        self.assertEqual("individual", listing["developer_identity"]["mode"])
        self.assertEqual("PENDING_USER_VERIFICATION", listing["developer_identity"]["status"])
        self.assertEqual("ALL_PORTAL_AVAILABLE", listing["availability"])
        self.assertFalse(listing["has_mcp"])
        self.assertFalse(listing["has_ui"])
        self.assertFalse(listing["requires_account"])
        self.assertFalse(listing["has_telemetry"])
        self.assertEqual([], listing["screenshots"])
        self.assertEqual("vgtree-plugin-1.1.0.zip", listing["bundle"]["filename"])
        self.assertEqual("SHA256SUMS", listing["bundle"]["digest_source"])

    def test_starter_prompts_cover_five_high_value_workflows(self) -> None:
        prompts = self.listing["starter_prompts"]
        self.assertEqual(5, len(prompts))
        self.assertEqual(
            {
                "capability-map",
                "wide-pass-execution",
                "receipt-verification",
                "obsidian-read-only-audit",
                "uid-first-knowledge-architecture",
            },
            {prompt["id"] for prompt in prompts},
        )
        self.assertTrue(all(prompt["prompt"].strip() for prompt in prompts))

    def test_plugin_manifest_uses_the_exact_public_listing_copy(self) -> None:
        manifest = json.loads(
            (ROOT / "plugins" / "vgtree" / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        interface = manifest["interface"]
        self.assertEqual(self.listing["short_description"], interface["shortDescription"])
        self.assertEqual(self.listing["long_description"], interface["longDescription"])
        self.assertEqual(
            [item["prompt"] for item in self.listing["starter_prompts"]],
            interface["defaultPrompt"],
        )

    def test_five_positive_and_three_negative_cases_are_reproducible(self) -> None:
        cases = self.cases["cases"]
        positives = [case for case in cases if case["polarity"] == "positive"]
        negatives = [case for case in cases if case["polarity"] == "negative"]
        self.assertEqual(5, len(positives))
        self.assertEqual(3, len(negatives))
        self.assertEqual(8, len({case["id"] for case in cases}))
        for case in positives:
            self.assertTrue(case["user_prompt"])
            self.assertTrue(case["expected_behavior"])
            self.assertTrue(case["expected_result_shape"])
            self.assertTrue(case["fixture"])
        for case in negatives:
            self.assertTrue(case["user_prompt"])
            self.assertTrue(case["expected_safe_fallback"])
            self.assertTrue(case["why_not_complete"])
            self.assertTrue(case["fixture"])

    def test_submission_validator_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/validate_submission.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(5, result["positive_cases"])
        self.assertEqual(3, result["negative_cases"])
        self.assertEqual(6, result["skills"])


if __name__ == "__main__":
    unittest.main()
