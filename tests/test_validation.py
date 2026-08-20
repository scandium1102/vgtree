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
        "history": [],
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


class StateValidationTests(unittest.TestCase):
    def test_valid_state_passes(self) -> None:
        report = validate_state(valid_state())
        self.assertTrue(report.valid, report.issues)

    def test_nested_unknown_branch_property_is_rejected(self) -> None:
        state = valid_state()
        state["branches"][0]["trust_me"] = True

        self.assertFalse(validate_state(state).valid)

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


if __name__ == "__main__":
    unittest.main()
