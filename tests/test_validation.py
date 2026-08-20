from __future__ import annotations

import copy
import unittest

from vgtree.validation import validate_evidence, validate_state, validate_task


def valid_task() -> dict:
    return {
        "task_id": "task-001",
        "title": "Ship a verified feature",
        "explicit_class": "T2",
        "signals": {
            "estimated_files": 3,
            "migration": False,
            "project_scale": False,
            "external_effect": False,
            "destructive": False,
            "cross_system": False,
            "irreversible": False,
        },
        "branches": [
            {
                "id": "primary-build",
                "title": "Build the product",
                "kind": "primary",
                "priority": "P0",
                "depends_on": [],
            },
            {
                "id": "secondary-docs",
                "title": "Document the product",
                "kind": "secondary",
                "priority": "P1",
                "depends_on": ["primary-build"],
            },
        ],
    }


def valid_state() -> dict:
    return {
        "schema_version": "2.0",
        "engine_version": "1.0.0",
        "workflow_ref": "WF-VEGA-TREE@1.0",
        "task": valid_task(),
        "task_class": "T2",
        "route": "tree",
        "phase": "branch_execution",
        "branches": [
            {
                "id": "primary-build",
                "title": "Build the product",
                "kind": "primary",
                "priority": "P0",
                "status": "IN_PROGRESS",
                "depends_on": [],
                "evidence": [],
            },
            {
                "id": "secondary-docs",
                "title": "Document the product",
                "kind": "secondary",
                "priority": "P1",
                "status": "PENDING",
                "depends_on": ["primary-build"],
                "evidence": [],
            },
        ],
        "evidence": [],
        "history": [
            {
                "from": None,
                "to": "mission_understanding",
                "timestamp": "2026-08-20T00:00:00Z",
                "reason": "workflow initialized",
            },
            {
                "from": "mission_understanding",
                "to": "outcome_definition",
                "timestamp": "2026-08-20T00:00:01Z",
                "reason": "computed phase gate passed",
            },
            {
                "from": "outcome_definition",
                "to": "breadth_mapping",
                "timestamp": "2026-08-20T00:00:02Z",
                "reason": "computed phase gate passed",
            },
            {
                "from": "breadth_mapping",
                "to": "branch_execution",
                "timestamp": "2026-08-20T00:00:03Z",
                "reason": "computed phase gate passed",
            },
        ],
    }


class TaskValidationTests(unittest.TestCase):
    def test_valid_task_passes(self) -> None:
        report = validate_task(valid_task())
        self.assertTrue(report.valid, report.issues)

    def test_passing_evidence_requires_digest_or_reference(self) -> None:
        item = {
            "id": "ev-1",
            "type": "test",
            "subject": "artifact",
            "method": "test command",
            "timestamp": "2026-08-20T00:00:00Z",
            "outcome": "PASS",
        }

        without_provenance = validate_evidence(item)
        item["reference"] = "ci://run/123"
        with_reference = validate_evidence(item)

        self.assertFalse(without_provenance.valid)
        self.assertTrue(with_reference.valid, with_reference.issues)

    def test_non_integer_estimated_files_is_controlled_failure(self) -> None:
        task = valid_task()
        task["signals"]["estimated_files"] = "many"

        report = validate_task(task)

        self.assertFalse(report.valid)
        self.assertIn("SCHEMA_INVALID", {issue.code for issue in report.issues})

    def test_nested_unknown_task_property_is_rejected(self) -> None:
        task = valid_task()
        task["signals"]["trust_me"] = True

        self.assertFalse(validate_task(task).valid)

    def test_command_adjacent_identifiers_reject_shell_metacharacters(self) -> None:
        task = valid_task()
        task["task_id"] = "task;whoami"
        self.assertFalse(validate_task(task).valid)

        task = valid_task()
        task["branches"] = [
            {
                "id": "build&whoami",
                "title": "Build",
                "kind": "primary",
                "priority": "P0",
                "depends_on": [],
            }
        ]
        self.assertFalse(validate_task(task).valid)

    def test_invalid_date_time_is_rejected(self) -> None:
        item = {
            "id": "ev-1",
            "type": "test",
            "subject": "artifact",
            "method": "test command",
            "timestamp": "not-a-date",
            "outcome": "PASS",
            "reference": "ci://run/123",
        }

        self.assertFalse(validate_evidence(item).valid)


class StateValidationTests(unittest.TestCase):
    def test_valid_state_passes(self) -> None:
        report = validate_state(valid_state())
        self.assertTrue(report.valid, report.issues)

    def test_nested_unknown_branch_property_is_rejected(self) -> None:
        state = valid_state()
        state["branches"][0]["trust_me"] = True

        self.assertFalse(validate_state(state).valid)

    def test_required_task_branch_cannot_be_removed_from_state(self) -> None:
        state = valid_state()
        state["branches"] = [state["branches"][1]]

        report = validate_state(state)

        self.assertIn("BRANCH_SPEC_MISSING", {issue.code for issue in report.issues})

    def test_primary_task_branch_cannot_be_demoted_in_state(self) -> None:
        state = valid_state()
        state["branches"][0]["kind"] = "secondary"

        report = validate_state(state)

        self.assertIn("BRANCH_SPEC_MISMATCH", {issue.code for issue in report.issues})

    def test_task_branch_dependency_cannot_be_changed_in_state(self) -> None:
        state = valid_state()
        state["branches"][1]["depends_on"] = []

        report = validate_state(state)

        self.assertIn("BRANCH_SPEC_MISMATCH", {issue.code for issue in report.issues})

    def test_task_branch_completion_spec_cannot_be_changed_in_state(self) -> None:
        state = valid_state()
        state["task"]["branches"][0]["definition_of_done"] = ["Tests pass"]
        state["branches"][0]["definition_of_done"] = ["Skip tests"]

        report = validate_state(state)

        self.assertIn("BRANCH_SPEC_MISMATCH", {issue.code for issue in report.issues})

    def test_derived_default_branch_is_bound_to_task(self) -> None:
        state = valid_state()
        state["task"].pop("branches")
        state["branches"] = [
            {
                "id": "primary-outcome",
                "title": state["task"]["title"],
                "kind": "primary",
                "priority": "P0",
                "status": "PENDING",
                "depends_on": [],
                "evidence": [],
            }
        ]

        self.assertTrue(validate_state(state).valid)
        state["branches"].clear()
        report = validate_state(state)
        self.assertIn("BRANCH_SPEC_MISSING", {issue.code for issue in report.issues})

    def test_primary_branch_cannot_be_deferred(self) -> None:
        state = valid_state()
        state["branches"][0]["priority"] = "DEFERRED"

        report = validate_state(state)

        self.assertIn("PRIMARY_DEFERRED", {issue.code for issue in report.issues})

    def test_dangling_dependency_is_rejected(self) -> None:
        state = valid_state()
        state["branches"][1]["depends_on"] = ["missing"]

        report = validate_state(state)

        self.assertIn("DEPENDENCY_MISSING", {issue.code for issue in report.issues})

    def test_self_dependency_is_rejected(self) -> None:
        state = valid_state()
        state["branches"][0]["depends_on"] = ["primary-build"]

        report = validate_state(state)

        self.assertIn("DEPENDENCY_SELF", {issue.code for issue in report.issues})

    def test_dependency_cycle_is_rejected(self) -> None:
        state = valid_state()
        state["branches"][0]["depends_on"] = ["secondary-docs"]

        report = validate_state(state)

        self.assertIn("DEPENDENCY_CYCLE", {issue.code for issue in report.issues})

    def test_duplicate_branch_id_is_rejected(self) -> None:
        state = valid_state()
        duplicate = copy.deepcopy(state["branches"][0])
        state["branches"].append(duplicate)

        report = validate_state(state)

        self.assertIn("BRANCH_ID_DUPLICATE", {issue.code for issue in report.issues})

    def test_blocked_branch_requires_reason_and_evidence(self) -> None:
        state = valid_state()
        state["branches"][0]["status"] = "BLOCKED"

        report = validate_state(state)

        codes = {issue.code for issue in report.issues}
        self.assertIn("BLOCKED_REASON_REQUIRED", codes)
        self.assertIn("BLOCKED_EVIDENCE_REQUIRED", codes)

    def test_accepted_limitation_requires_record_and_evidence(self) -> None:
        state = valid_state()
        state["branches"][0]["status"] = "ACCEPTED_LIMITATION"

        report = validate_state(state)

        codes = {issue.code for issue in report.issues}
        self.assertIn("LIMITATION_RECORD_REQUIRED", codes)
        self.assertIn("LIMITATION_EVIDENCE_REQUIRED", codes)

    def test_task_class_must_match_computed_minimum(self) -> None:
        state = valid_state()
        state["task"]["signals"]["migration"] = True
        state["task_class"] = "T0"

        report = validate_state(state)

        self.assertIn("TASK_CLASS_MISMATCH", {issue.code for issue in report.issues})

    def test_tree_state_rejects_non_tree_route(self) -> None:
        state = valid_state()
        state["route"] = "direct"

        self.assertFalse(validate_state(state).valid)

    def test_phase_must_match_history(self) -> None:
        state = valid_state()
        state["phase"] = "integration"

        report = validate_state(state)

        self.assertIn("HISTORY_PHASE_MISMATCH", {issue.code for issue in report.issues})

    def test_complete_phase_requires_terminal_branches_and_evidence(self) -> None:
        state = valid_state()
        state["phase"] = "complete"
        state["history"].extend(
            [
                {
                    "from": "branch_execution",
                    "to": "integration",
                    "timestamp": "2026-08-20T00:00:04Z",
                    "reason": "computed phase gate passed",
                },
                {
                    "from": "integration",
                    "to": "verification",
                    "timestamp": "2026-08-20T00:00:05Z",
                    "reason": "computed phase gate passed",
                },
                {
                    "from": "verification",
                    "to": "complete",
                    "timestamp": "2026-08-20T00:00:06Z",
                    "reason": "computed phase gate passed",
                },
            ]
        )

        report = validate_state(state)

        codes = {issue.code for issue in report.issues}
        self.assertIn("PHASE_BRANCH_GATE_UNSATISFIED", codes)
        self.assertIn("PHASE_INTEGRATION_EVIDENCE_REQUIRED", codes)
        self.assertIn("PHASE_FINAL_EVIDENCE_REQUIRED", codes)

    def test_maximum_depth_dag_is_validated_iteratively(self) -> None:
        state = valid_state()
        branches = []
        for index in reversed(range(1000)):
            branches.append(
                {
                    "id": f"b-{index}",
                    "title": "Bounded branch",
                    "kind": "secondary",
                    "priority": "P1",
                    "status": "PENDING",
                    "depends_on": [f"b-{index - 1}"] if index else [],
                    "evidence": [],
                }
            )
        state["branches"] = branches
        state["task"]["branches"] = [
            {
                key: branch[key]
                for key in ("id", "title", "kind", "priority", "depends_on")
            }
            for branch in branches
        ]

        report = validate_state(state)

        self.assertTrue(report.valid, report.issues)

    def test_branch_count_is_bounded(self) -> None:
        task = valid_task()
        task["branches"] = [
            {
                "id": f"b-{index}",
                "title": "Bounded branch",
                "kind": "secondary",
                "priority": "P1",
                "depends_on": [],
            }
            for index in range(1001)
        ]

        self.assertFalse(validate_task(task).valid)


if __name__ == "__main__":
    unittest.main()
