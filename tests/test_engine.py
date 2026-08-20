from __future__ import annotations

import copy
import unittest

from vgtree.engine import VGTREEEngine

from test_validation import valid_task


def evidence(evidence_id: str, evidence_type: str) -> dict:
    return {
        "id": evidence_id,
        "type": evidence_type,
        "subject": "task-001",
        "method": "automated test",
        "timestamp": "2026-08-20T00:00:00Z",
        "outcome": "PASS",
    }


def initialized_state() -> dict:
    task = valid_task()
    task["branches"] = [
        {
            "id": "build",
            "title": "Build",
            "kind": "primary",
            "priority": "P0",
            "depends_on": [],
        },
        {
            "id": "docs",
            "title": "Document",
            "kind": "secondary",
            "priority": "P1",
            "depends_on": ["build"],
        },
    ]
    result = VGTREEEngine().initialize(task)
    assert result.status == "PASS"
    return result.data["state"]


class EngineInitializationTests(unittest.TestCase):
    def test_initialize_builds_strict_state(self) -> None:
        state = initialized_state()

        self.assertEqual(state["schema_version"], "2.0")
        self.assertEqual(state["phase"], "mission_understanding")
        self.assertEqual(state["branches"][0]["status"], "PENDING")

    def test_invalid_task_returns_fail_without_exception(self) -> None:
        task = valid_task()
        task["signals"]["estimated_files"] = "many"

        result = VGTREEEngine().initialize(task)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.code, "TASK_INVALID")

    def test_branch_definition_of_done_and_evidence_plan_are_preserved(self) -> None:
        task = valid_task()
        task["branches"] = [
            {
                "id": "build",
                "title": "Build",
                "kind": "primary",
                "priority": "P0",
                "depends_on": [],
                "definition_of_done": ["Feature works", "Regression suite passes"],
                "evidence_requirements": ["test report", "artifact digest"],
                "stop_condition": "Stop after two probes without a decision delta.",
            }
        ]

        result = VGTREEEngine().initialize(task)

        self.assertEqual(result.status, "PASS", result)
        branch = result.data["state"]["branches"][0]
        self.assertEqual(branch["definition_of_done"][0], "Feature works")
        self.assertEqual(branch["evidence_requirements"][0], "test report")
        self.assertEqual(
            branch["stop_condition"], "Stop after two probes without a decision delta."
        )


class EngineTransitionTests(unittest.TestCase):
    def test_early_phases_advance_in_order(self) -> None:
        state = initialized_state()
        engine = VGTREEEngine()

        for expected in ("outcome_definition", "breadth_mapping", "branch_execution"):
            result = engine.next(state)
            self.assertEqual(result.status, "PASS", result)
            state = result.data["state"]
            self.assertEqual(state["phase"], expected)

    def test_branch_execution_waits_for_primary_branch(self) -> None:
        state = initialized_state()
        state["phase"] = "branch_execution"
        state["branches"][0]["status"] = "IN_PROGRESS"

        result = VGTREEEngine().next(state)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.code, "BRANCHES_INCOMPLETE")

    def test_blocked_primary_branch_blocks_advancement(self) -> None:
        state = initialized_state()
        state["phase"] = "branch_execution"
        state["branches"][0].update(
            {
                "status": "BLOCKED",
                "blocked_reason": "Missing external permission",
                "evidence": [evidence("ev-block", "blocker")],
            }
        )

        result = VGTREEEngine().next(state)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.code, "PRIMARY_BRANCH_BLOCKED")

    def test_accepted_limitation_can_satisfy_primary_branch(self) -> None:
        state = initialized_state()
        state["phase"] = "branch_execution"
        state["branches"][0].update(
            {
                "status": "ACCEPTED_LIMITATION",
                "evidence": [evidence("ev-limit", "limitation-acceptance")],
                "limitation": {
                    "scope": "One optional integration",
                    "consequence": "Manual setup remains",
                    "owner": "maintainer",
                    "accepted_at": "2026-08-20T00:00:00Z",
                },
            }
        )

        result = VGTREEEngine().next(state)

        self.assertEqual(result.status, "PASS", result)
        self.assertEqual(result.data["state"]["phase"], "integration")

    def test_integration_requires_integration_evidence(self) -> None:
        state = initialized_state()
        state["phase"] = "integration"
        state["branches"][0]["status"] = "VERIFIED"

        result = VGTREEEngine().next(state)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.code, "INTEGRATION_EVIDENCE_REQUIRED")

    def test_verification_requires_final_evidence(self) -> None:
        state = initialized_state()
        state["phase"] = "verification"
        state["branches"][0]["status"] = "VERIFIED"
        state["evidence"] = [evidence("ev-integration", "integration")]

        result = VGTREEEngine().complete(state)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.code, "FINAL_EVIDENCE_REQUIRED")

    def test_complete_requires_prior_integration_evidence(self) -> None:
        state = initialized_state()
        state["phase"] = "verification"
        state["branches"][0]["status"] = "VERIFIED"
        state["evidence"] = [evidence("ev-final", "final-verification")]

        result = VGTREEEngine().complete(state)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.code, "INTEGRATION_EVIDENCE_REQUIRED")

    def test_complete_succeeds_only_from_verification(self) -> None:
        state = initialized_state()
        state["phase"] = "verification"
        state["branches"][0]["status"] = "VERIFIED"
        state["evidence"] = [
            evidence("ev-integration", "integration"),
            evidence("ev-final", "final-verification"),
        ]

        result = VGTREEEngine().complete(state)

        self.assertEqual(result.status, "PASS", result)
        self.assertEqual(result.code, "COMPLETE")
        self.assertEqual(result.data["state"]["phase"], "complete")

    def test_complete_rejects_earlier_phase_even_with_evidence(self) -> None:
        state = initialized_state()
        state["phase"] = "mission_understanding"
        state["branches"][0]["status"] = "VERIFIED"
        state["evidence"] = [evidence("ev-final", "final-verification")]

        result = VGTREEEngine().complete(state)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.code, "ILLEGAL_PHASE")


class GuardTests(unittest.TestCase):
    def test_guard_blocks_unsatisfied_dependency(self) -> None:
        state = initialized_state()

        result = VGTREEEngine().guard(state, "docs", "write guide")

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.code, "DEPENDENCY_UNSATISFIED")

    def test_guard_passes_after_dependency_is_verified(self) -> None:
        state = initialized_state()
        state["branches"][0]["status"] = "VERIFIED"

        result = VGTREEEngine().guard(state, "docs", "write guide")

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.code, "BRANCH_GUARD_PASS")

    def test_guard_rejects_invalid_state(self) -> None:
        state = initialized_state()
        invalid = copy.deepcopy(state)
        invalid["phase"] = "invented"

        result = VGTREEEngine().guard(invalid, "build", "work")

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.code, "STATE_INVALID")


class BranchMutationTests(unittest.TestCase):
    def test_record_evidence_then_verify_branch(self) -> None:
        state = initialized_state()
        engine = VGTREEEngine()
        started = engine.set_branch(state, "build", "IN_PROGRESS")
        state = started.data["state"]
        recorded = engine.record_evidence(
            state, evidence("ev-build", "test"), branch_id="build"
        )
        state = recorded.data["state"]

        verified = engine.set_branch(state, "build", "VERIFIED")

        self.assertEqual(verified.status, "PASS", verified)
        self.assertEqual(verified.data["state"]["branches"][0]["status"], "VERIFIED")

    def test_verify_branch_without_passing_evidence_is_rejected(self) -> None:
        state = initialized_state()
        state["branches"][0]["status"] = "IN_PROGRESS"

        result = VGTREEEngine().set_branch(state, "build", "VERIFIED")

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.code, "BRANCH_EVIDENCE_REQUIRED")

    def test_duplicate_evidence_id_is_rejected(self) -> None:
        state = initialized_state()
        first = VGTREEEngine().record_evidence(state, evidence("ev-1", "test"))

        second = VGTREEEngine().record_evidence(
            first.data["state"], evidence("ev-1", "test")
        )

        self.assertEqual(second.status, "FAIL")
        self.assertEqual(second.code, "EVIDENCE_ID_DUPLICATE")

    def test_blocked_status_requires_reason_and_evidence(self) -> None:
        state = initialized_state()

        result = VGTREEEngine().set_branch(
            state, "build", "BLOCKED", blocked_reason="Permission missing"
        )

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.code, "BRANCH_EVIDENCE_REQUIRED")

    def test_illegal_terminal_transition_is_rejected(self) -> None:
        state = initialized_state()
        state["branches"][0]["status"] = "VERIFIED"
        state["branches"][0]["evidence"] = [evidence("ev-build", "test")]

        result = VGTREEEngine().set_branch(state, "build", "IN_PROGRESS")

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.code, "BRANCH_TRANSITION_ILLEGAL")


if __name__ == "__main__":
    unittest.main()
