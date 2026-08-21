from __future__ import annotations

import copy
import unittest

from test_capability import valid_map
from vgtree.capability import compile_capability_map
from vgtree.coverage import compute_coverage
from vgtree.engine import VGTREEEngine
from vgtree.validation import validate_state


def coverage_task(policy: str = "REQUIRED") -> dict:
    result = compile_capability_map(
        valid_map(policy), source_digest="sha256:" + ("1" * 64)
    )
    assert result.status == "PASS", result
    return result.data["task"]


def baseline(branch_id: str, method: str, suffix: str = "1") -> dict:
    return {
        "id": f"baseline-{branch_id}-{suffix}",
        "type": "baseline",
        "subject": f"branch:{branch_id}:baseline",
        "method": method,
        "timestamp": "2026-08-20T00:00:00Z",
        "outcome": "PASS",
        "digest": "sha256:" + (suffix * 64),
    }


def at_branch_execution(state: dict) -> dict:
    engine = VGTREEEngine()
    current = state
    while current["phase"] != "branch_execution":
        result = engine.next(current)
        assert result.status == "PASS", result
        current = result.data["state"]
    return current


def covered_state(policy: str = "REQUIRED") -> dict:
    engine = VGTREEEngine()
    state = at_branch_execution(engine.initialize(coverage_task(policy)).data["state"])
    for index, branch in enumerate(state["branches"], start=1):
        for requirement in branch["baseline_evidence_requirements"]:
            branch["evidence"].append(baseline(branch["id"], requirement, str(index)))
    return state


class CoverageInitializationTests(unittest.TestCase):
    def test_initialize_opted_in_task_uses_state_2_1(self) -> None:
        result = VGTREEEngine().initialize(coverage_task())
        self.assertEqual(result.status, "PASS", result)
        state = result.data["state"]
        self.assertEqual(state["schema_version"], "2.1")
        self.assertEqual(state["coverage"]["execution_stage"], "WIDE")
        self.assertTrue(validate_state(state).valid)

    def test_schema_2_0_rejects_coverage_features(self) -> None:
        state = VGTREEEngine().initialize(coverage_task()).data["state"]
        state["schema_version"] = "2.0"
        codes = {item.code for item in validate_state(state).issues}
        self.assertIn("STATE_VERSION_FEATURE_MISMATCH", codes)

    def test_runtime_baseline_spec_is_immutable(self) -> None:
        state = VGTREEEngine().initialize(coverage_task()).data["state"]
        state["branches"][0]["minimum_viable_state"] = ["Easier baseline"]
        codes = {item.code for item in validate_state(state).issues}
        self.assertIn("BRANCH_SPEC_MISMATCH", codes)


class CoverageCalculationTests(unittest.TestCase):
    def test_coverage_requires_every_exact_method(self) -> None:
        state = VGTREEEngine().initialize(coverage_task()).data["state"]
        missing = VGTREEEngine().evaluate_coverage(state)
        for index, branch in enumerate(state["branches"], start=1):
            branch["evidence"].append(
                baseline(
                    branch["id"], branch["baseline_evidence_requirements"][0], str(index)
                )
            )
        ready = VGTREEEngine().evaluate_coverage(state)
        self.assertEqual(missing.code, "COVERAGE_INCOMPLETE")
        self.assertEqual(missing.status, "BLOCKED")
        self.assertEqual(ready.code, "WIDE_PASS_READY")
        self.assertEqual(ready.data["coverage_ratio"], 1.0)

    def test_wrong_subject_does_not_count(self) -> None:
        state = VGTREEEngine().initialize(coverage_task()).data["state"]
        item = baseline("authorize", "Fresh authorization record")
        item["subject"] = "branch:deploy:baseline"
        state["branches"][0]["evidence"].append(item)
        self.assertIn("authorize", compute_coverage(state)["missing_branches"])


class CoverageTransitionTests(unittest.TestCase):
    def test_required_transition_blocks_until_ready(self) -> None:
        engine = VGTREEEngine()
        state = at_branch_execution(engine.initialize(coverage_task()).data["state"])
        blocked = engine.advance_execution_depth(state)
        passed = engine.advance_execution_depth(covered_state())
        self.assertEqual(blocked.code, "COVERAGE_INCOMPLETE")
        self.assertEqual(passed.code, "DEEP_STAGE_ACTIVATED")
        self.assertEqual(passed.data["state"]["coverage"]["execution_stage"], "DEEP")

    def test_advisory_override_requires_reason(self) -> None:
        engine = VGTREEEngine()
        state = at_branch_execution(
            engine.initialize(coverage_task("ADVISORY")).data["state"]
        )
        missing = engine.advance_execution_depth(state)
        override = engine.advance_execution_depth(
            state, reason="One baseline is externally blocked"
        )
        self.assertEqual(missing.code, "COVERAGE_OVERRIDE_REASON_REQUIRED")
        self.assertEqual(override.status, "PASS")
        self.assertTrue(override.data["state"]["coverage"]["history"][0]["override"])

    def test_opted_in_guard_requires_depth(self) -> None:
        state = VGTREEEngine().initialize(coverage_task()).data["state"]
        result = VGTREEEngine().guard(state, "authorize", "implement component")
        self.assertEqual(result.code, "DEPTH_REQUIRED")

    def test_deep_guard_blocks_in_wide_stage(self) -> None:
        state = VGTREEEngine().initialize(coverage_task()).data["state"]
        result = VGTREEEngine().guard(
            state, "authorize", "optimize component", depth="deep"
        )
        self.assertEqual(result.code, "DEEP_STAGE_NOT_ACTIVE")

    def test_required_deep_state_cannot_lose_baseline_evidence(self) -> None:
        advanced = VGTREEEngine().advance_execution_depth(covered_state()).data["state"]
        tampered = copy.deepcopy(advanced)
        tampered["branches"][0]["evidence"] = []
        codes = {item.code for item in validate_state(tampered).issues}
        self.assertIn("COVERAGE_STAGE_INVALID", codes)


if __name__ == "__main__":
    unittest.main()
