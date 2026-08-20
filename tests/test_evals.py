from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_v1_1_evals.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_v1_1_evals", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class V11EvaluationTests(unittest.TestCase):
    def test_five_required_families_exist(self) -> None:
        expected = {"website", "vision", "research", "ros-observer", "agent-runtime"}
        actual = {
            path.parent.name
            for path in (ROOT / "evals" / "v1.1").glob("*/manifest.json")
        }
        self.assertEqual(actual, expected)

    def test_every_manifest_has_exact_contract(self) -> None:
        module = load_validator()
        for path in (ROOT / "evals" / "v1.1").glob("*/manifest.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(module.validate_manifest(value), [], path.name)

    def test_context_budget_metrics_are_bounded_and_descriptive(self) -> None:
        module = load_validator()
        catalog = json.loads(
            (ROOT / "evals" / "v1.1" / "context-budget" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        selection = json.loads(
            (ROOT / "evals" / "v1.1" / "context-budget" / "selection.json").read_text(
                encoding="utf-8"
            )
        )
        errors, metrics = module.validate_context_budget(catalog, selection)
        self.assertEqual(errors, [])
        self.assertEqual(metrics["full_catalog_count"], 50)
        self.assertEqual(metrics["active_bundle_count"], 2)
        self.assertEqual(metrics["unnecessary_inspections"], [])
        self.assertNotIn("improvement_percentage", metrics)

    def test_behavioral_result_requires_environment_disclosure(self) -> None:
        module = load_validator()
        value = json.loads(
            (ROOT / "evals" / "v1.1" / "behavioral-result.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(module.validate_behavioral_result(value), [])
        del value["model"]["reasoning"]
        self.assertIn("model.reasoning is required", module.validate_behavioral_result(value))

    def test_validator_cli_passes_all_deterministic_fixtures(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["measured_behavioral_results"], 0)


if __name__ == "__main__":
    unittest.main()
