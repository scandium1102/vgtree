"""VGTREE execution engine and computed workflow gates."""

from __future__ import annotations

import copy
from collections.abc import Collection
from datetime import datetime, timezone
from typing import Any

from vgtree import __version__
from vgtree.models import Decision, GuardResult, ValidationReport
from vgtree.routing import TREE_WORKFLOW_REF, classify_task
from vgtree.validation import validate_evidence, validate_state, validate_task


PHASES = (
    "mission_understanding",
    "outcome_definition",
    "breadth_mapping",
    "branch_execution",
    "integration",
    "verification",
    "complete",
)
TERMINAL_BRANCH_STATUSES = {"VERIFIED", "ACCEPTED_LIMITATION"}
BRANCH_TRANSITIONS = {
    "PENDING": {"IN_PROGRESS", "BLOCKED"},
    "IN_PROGRESS": {"VERIFIED", "BLOCKED", "ACCEPTED_LIMITATION"},
    "BLOCKED": {"IN_PROGRESS", "ACCEPTED_LIMITATION"},
    "VERIFIED": set(),
    "ACCEPTED_LIMITATION": set(),
}


class VGTREEEngine:
    def __init__(self, *, registered_workflows: Collection[str] = ()) -> None:
        self.registered_workflows = frozenset(registered_workflows)

    def classify(self, task: dict[str, Any]) -> Decision:
        return classify_task(task, registered_workflows=self.registered_workflows)

    def initialize(self, task: dict[str, Any]) -> GuardResult:
        report = validate_task(task)
        if not report.valid:
            return GuardResult(
                status="FAIL",
                code="TASK_INVALID",
                message="Task specification failed validation.",
                data={"validation": report.as_dict()},
            )

        decision = self.classify(task)
        branch_specs = task.get("branches") or [
            {
                "id": "primary-outcome",
                "title": task["title"],
                "kind": "primary",
                "priority": "P0",
                "depends_on": [],
            }
        ]
        branches = [
            {
                **copy.deepcopy(branch),
                "status": "PENDING",
                "evidence": [],
            }
            for branch in branch_specs
        ]
        state = {
            "schema_version": "2.0",
            "engine_version": __version__,
            "workflow_ref": TREE_WORKFLOW_REF,
            "task": copy.deepcopy(task),
            "task_class": decision.task_class,
            "route": decision.route,
            "phase": "mission_understanding",
            "branches": branches,
            "evidence": [],
            "history": [
                {
                    "from": None,
                    "to": "mission_understanding",
                    "timestamp": _timestamp(),
                    "reason": "workflow initialized",
                }
            ],
        }
        state_report = validate_state(state)
        if not state_report.valid:
            return GuardResult(
                status="FAIL",
                code="STATE_INVALID",
                message="Initialized state failed validation.",
                data={"validation": state_report.as_dict()},
            )
        return GuardResult(
            status="PASS",
            code="INITIALIZED",
            message="Workflow state initialized.",
            data={"decision": decision.as_dict(), "state": state},
        )

    def validate(self, state: Any) -> ValidationReport:
        return validate_state(state)

    def record_evidence(
        self,
        state: dict[str, Any],
        evidence: dict[str, Any],
        *,
        branch_id: str | None = None,
    ) -> GuardResult:
        invalid = self._invalid_state_result(state)
        if invalid:
            return invalid
        evidence_report = validate_evidence(evidence)
        if not evidence_report.valid:
            return GuardResult(
                "FAIL",
                "EVIDENCE_INVALID",
                "Evidence record failed validation.",
                {"validation": evidence_report.as_dict()},
            )
        evidence_ids = {
            item["id"]
            for item in state["evidence"]
            if isinstance(item, dict) and "id" in item
        }
        for branch in state["branches"]:
            evidence_ids.update(
                item["id"]
                for item in branch["evidence"]
                if isinstance(item, dict) and "id" in item
            )
        if evidence["id"] in evidence_ids:
            return GuardResult(
                "FAIL",
                "EVIDENCE_ID_DUPLICATE",
                f"Evidence id already exists: {evidence['id']}",
            )

        updated = copy.deepcopy(state)
        if branch_id is None:
            updated["evidence"].append(copy.deepcopy(evidence))
        else:
            branch = _find_branch(updated, branch_id)
            if branch is None:
                return GuardResult(
                    "FAIL", "BRANCH_NOT_FOUND", f"Unknown branch: {branch_id}"
                )
            branch["evidence"].append(copy.deepcopy(evidence))
        return GuardResult(
            "PASS",
            "EVIDENCE_RECORDED",
            "Evidence record attached to workflow state.",
            {"state": updated, "evidence_id": evidence["id"], "branch_id": branch_id},
        )

    def set_branch(
        self,
        state: dict[str, Any],
        branch_id: str,
        status: str,
        *,
        blocked_reason: str | None = None,
        limitation: dict[str, Any] | None = None,
    ) -> GuardResult:
        invalid = self._invalid_state_result(state)
        if invalid:
            return invalid
        if status not in BRANCH_TRANSITIONS:
            return GuardResult(
                "FAIL", "BRANCH_STATUS_INVALID", f"Unsupported branch status: {status}"
            )
        current_branch = _find_branch(state, branch_id)
        if current_branch is None:
            return GuardResult("FAIL", "BRANCH_NOT_FOUND", f"Unknown branch: {branch_id}")
        current_status = current_branch["status"]
        if status == current_status:
            return GuardResult(
                "PASS", "BRANCH_UNCHANGED", "Branch already has the requested status.", {"state": state}
            )
        if status not in BRANCH_TRANSITIONS[current_status]:
            return GuardResult(
                "FAIL",
                "BRANCH_TRANSITION_ILLEGAL",
                f"Cannot change branch from {current_status} to {status}.",
            )
        if status in {"VERIFIED", "BLOCKED", "ACCEPTED_LIMITATION"}:
            evidence_records = current_branch["evidence"]
            if not evidence_records:
                return GuardResult(
                    "REVIEW_REQUIRED",
                    "BRANCH_EVIDENCE_REQUIRED",
                    "Terminal and blocked branch states require evidence.",
                )
            if status == "VERIFIED" and not any(
                item.get("outcome") == "PASS" for item in evidence_records
            ):
                return GuardResult(
                    "REVIEW_REQUIRED",
                    "BRANCH_PASS_EVIDENCE_REQUIRED",
                    "Verified status requires at least one passing evidence record.",
                )
        if status == "BLOCKED" and not blocked_reason:
            return GuardResult(
                "REVIEW_REQUIRED",
                "BLOCKED_REASON_REQUIRED",
                "Blocked status requires a reason.",
            )
        if status == "ACCEPTED_LIMITATION" and not limitation:
            return GuardResult(
                "REVIEW_REQUIRED",
                "LIMITATION_RECORD_REQUIRED",
                "Accepted limitation status requires a structured limitation record.",
            )

        updated = copy.deepcopy(state)
        branch = _find_branch(updated, branch_id)
        assert branch is not None
        branch["status"] = status
        branch.pop("blocked_reason", None)
        branch.pop("limitation", None)
        if status == "BLOCKED":
            branch["blocked_reason"] = blocked_reason
        if status == "ACCEPTED_LIMITATION":
            branch["limitation"] = copy.deepcopy(limitation)
        report = validate_state(updated)
        if not report.valid:
            return GuardResult(
                "FAIL",
                "STATE_INVALID",
                "Branch update would create invalid state.",
                {"validation": report.as_dict()},
            )
        return GuardResult(
            "PASS",
            "BRANCH_UPDATED",
            f"Branch {branch_id} changed from {current_status} to {status}.",
            {"state": updated, "branch_id": branch_id, "status": status},
        )

    def next(self, state: dict[str, Any]) -> GuardResult:
        invalid = self._invalid_state_result(state)
        if invalid:
            return invalid

        phase = state["phase"]
        if phase == "complete":
            return GuardResult(
                "PASS", "ALREADY_COMPLETE", "Workflow is already complete.", {"state": state}
            )
        if phase in PHASES[:3]:
            return self._advance(state, PHASES[PHASES.index(phase) + 1])
        if phase == "branch_execution":
            return self._advance_from_branches(state)
        if phase == "integration":
            if not _has_passing_evidence(state, "integration"):
                return GuardResult(
                    "REVIEW_REQUIRED",
                    "INTEGRATION_EVIDENCE_REQUIRED",
                    "Passing integration evidence is required before verification.",
                )
            return self._advance(state, "verification")
        if phase == "verification":
            return self.complete(state)
        return GuardResult("FAIL", "ILLEGAL_PHASE", f"Unsupported phase: {phase}")

    def guard(
        self, state: dict[str, Any], branch_id: str, activity: str
    ) -> GuardResult:
        invalid = self._invalid_state_result(state)
        if invalid:
            return invalid
        if not activity.strip():
            return GuardResult("FAIL", "ACTIVITY_REQUIRED", "Activity must not be empty.")

        branches = {branch["id"]: branch for branch in state["branches"]}
        branch = branches.get(branch_id)
        if branch is None:
            return GuardResult("FAIL", "BRANCH_NOT_FOUND", f"Unknown branch: {branch_id}")
        if branch["status"] == "BLOCKED":
            return GuardResult(
                "BLOCKED",
                "BRANCH_BLOCKED",
                branch.get("blocked_reason", "Branch is blocked."),
            )
        if branch["priority"] == "DEFERRED":
            return GuardResult(
                "REVIEW_REQUIRED",
                "BRANCH_DEFERRED",
                "Deferred work requires explicit reprioritization.",
            )

        unsatisfied = [
            dependency
            for dependency in branch["depends_on"]
            if branches[dependency]["status"] not in TERMINAL_BRANCH_STATUSES
        ]
        if unsatisfied:
            return GuardResult(
                "BLOCKED",
                "DEPENDENCY_UNSATISFIED",
                "Branch dependencies are not terminal.",
                {"dependencies": unsatisfied},
            )

        if branch["kind"] == "secondary":
            pending_primary = [
                candidate["id"]
                for candidate in state["branches"]
                if candidate["kind"] == "primary"
                and candidate["priority"] == "P0"
                and candidate["status"] not in TERMINAL_BRANCH_STATUSES
            ]
            if pending_primary:
                return GuardResult(
                    "BLOCKED",
                    "PRIMARY_OUTCOME_PENDING",
                    "Primary P0 outcomes must be resolved before unrelated secondary work.",
                    {"branches": pending_primary},
                )

        return GuardResult(
            "PASS",
            "BRANCH_GUARD_PASS",
            "Branch activity is allowed.",
            {"branch_id": branch_id, "activity": activity},
        )

    def complete(self, state: dict[str, Any]) -> GuardResult:
        invalid = self._invalid_state_result(state)
        if invalid:
            return invalid
        if state["phase"] != "verification":
            return GuardResult(
                "FAIL",
                "ILLEGAL_PHASE",
                "Completion is only legal from the verification phase.",
            )

        branch_gate = self._branch_gate(state)
        if branch_gate:
            return branch_gate
        if not _has_passing_evidence(state, "integration"):
            return GuardResult(
                "REVIEW_REQUIRED",
                "INTEGRATION_EVIDENCE_REQUIRED",
                "Passing integration evidence is required before completion.",
            )
        if not _has_passing_evidence(state, "final-verification"):
            return GuardResult(
                "REVIEW_REQUIRED",
                "FINAL_EVIDENCE_REQUIRED",
                "Passing final-verification evidence is required.",
            )
        result = self._advance(state, "complete")
        return GuardResult(
            result.status,
            "COMPLETE",
            "Workflow completion gates passed.",
            result.data,
        )

    def _advance_from_branches(self, state: dict[str, Any]) -> GuardResult:
        gate = self._branch_gate(state)
        if gate:
            return gate
        return self._advance(state, "integration")

    def _branch_gate(self, state: dict[str, Any]) -> GuardResult | None:
        primary = [branch for branch in state["branches"] if branch["kind"] == "primary"]
        blocked = [branch["id"] for branch in primary if branch["status"] == "BLOCKED"]
        if blocked:
            return GuardResult(
                "BLOCKED",
                "PRIMARY_BRANCH_BLOCKED",
                "A primary branch remains blocked.",
                {"branches": blocked},
            )
        incomplete = [
            branch["id"]
            for branch in primary
            if branch["status"] not in TERMINAL_BRANCH_STATUSES
        ]
        if incomplete:
            return GuardResult(
                "REVIEW_REQUIRED",
                "BRANCHES_INCOMPLETE",
                "Primary branches are not verified or explicitly accepted.",
                {"branches": incomplete},
            )
        return None

    def _advance(self, state: dict[str, Any], target: str) -> GuardResult:
        current = state["phase"]
        if PHASES.index(target) != PHASES.index(current) + 1:
            return GuardResult(
                "FAIL", "ILLEGAL_TRANSITION", f"Cannot advance from {current} to {target}."
            )
        updated = copy.deepcopy(state)
        updated["phase"] = target
        updated["history"].append(
            {
                "from": current,
                "to": target,
                "timestamp": _timestamp(),
                "reason": "computed phase gate passed",
            }
        )
        return GuardResult(
            "PASS",
            "PHASE_ADVANCED",
            f"Workflow advanced to {target}.",
            {"state": updated},
        )

    def _invalid_state_result(self, state: Any) -> GuardResult | None:
        report = validate_state(state)
        if report.valid:
            return None
        return GuardResult(
            "FAIL",
            "STATE_INVALID",
            "Workflow state failed validation.",
            {"validation": report.as_dict()},
        )


def _has_passing_evidence(state: dict[str, Any], evidence_type: str) -> bool:
    return any(
        item.get("type") == evidence_type and item.get("outcome") == "PASS"
        for item in state.get("evidence", [])
        if isinstance(item, dict)
    )


def _find_branch(state: dict[str, Any], branch_id: str) -> dict[str, Any] | None:
    return next(
        (branch for branch in state.get("branches", []) if branch.get("id") == branch_id),
        None,
    )


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
