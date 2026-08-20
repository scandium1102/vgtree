"""Strict structural and semantic validation for VGTREE documents."""

from __future__ import annotations

import json
import re
from datetime import datetime
from importlib.resources import files
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

from vgtree.coverage import compute_coverage
from vgtree.dag import has_cycle
from vgtree.models import ValidationIssue, ValidationReport
from vgtree.semantics import compute_task_class


def _load_schema(name: str) -> dict[str, Any]:
    schema_path = files("vgtree").joinpath("schemas", name)
    return json.loads(schema_path.read_text(encoding="utf-8"))


TASK_SCHEMA = _load_schema("task.schema.json")
STATE_SCHEMA = _load_schema("state.schema.json")
FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_date_time(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


TASK_VALIDATOR = Draft202012Validator(TASK_SCHEMA, format_checker=FORMAT_CHECKER)
STATE_VALIDATOR = Draft202012Validator(STATE_SCHEMA, format_checker=FORMAT_CHECKER)
EVIDENCE_VALIDATOR = Draft202012Validator(
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "#/$defs/evidence",
        "$defs": STATE_SCHEMA["$defs"],
    },
    format_checker=FORMAT_CHECKER,
)

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
BRANCH_SPEC_FIELDS = (
    "id",
    "title",
    "kind",
    "priority",
    "depends_on",
    "definition_of_done",
    "evidence_requirements",
    "stop_condition",
    "coverage_required",
    "minimum_viable_state",
    "baseline_evidence_requirements",
    "shared_interfaces",
    "deferred_details",
)
COVERAGE_BRANCH_FIELDS = BRANCH_SPEC_FIELDS[-5:]


def _json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _schema_issues(validator: Draft202012Validator, value: Any) -> list[ValidationIssue]:
    return [
        ValidationIssue(
            code="SCHEMA_INVALID",
            path=_json_path(error.absolute_path),
            message=error.message,
        )
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    ]


def _report(issues: list[ValidationIssue]) -> ValidationReport:
    return ValidationReport(status="PASS" if not issues else "FAIL", issues=tuple(issues))


def validate_task(task: Any) -> ValidationReport:
    return _report(_schema_issues(TASK_VALIDATOR, task))


def validate_evidence(evidence: Any) -> ValidationReport:
    return _report(_schema_issues(EVIDENCE_VALIDATOR, evidence))


def validate_state(state: Any) -> ValidationReport:
    issues = _schema_issues(STATE_VALIDATOR, state)
    if not isinstance(state, dict):
        return _report(issues)

    task = state.get("task")
    task_report = validate_task(task)
    for issue in task_report.issues:
        issues.append(
            ValidationIssue(issue.code, f"$.task{issue.path[1:]}", issue.message)
        )

    branches = state.get("branches")
    if not isinstance(branches, list):
        return _report(issues)

    issues.extend(_branch_issues(branches))
    issues.extend(_history_issues(state))
    if task_report.valid:
        computed_class, _ = compute_task_class(task)
        if state.get("task_class") != computed_class:
            issues.append(
                ValidationIssue(
                    "TASK_CLASS_MISMATCH",
                    "$.task_class",
                    f"task_class must equal computed class {computed_class}.",
                )
            )
        issues.extend(_branch_spec_issues(task, branches))
    issues.extend(_coverage_state_issues(state))
    issues.extend(_phase_gate_issues(state, branches))
    return _report(_deduplicate(issues))


def _expected_branch_specs(task: dict[str, Any]) -> list[dict[str, Any]]:
    configured = task.get("branches")
    if isinstance(configured, list) and configured:
        return configured
    return [
        {
            "id": "primary-outcome",
            "title": task["title"],
            "kind": "primary",
            "priority": "P0",
            "depends_on": [],
        }
    ]


def _branch_spec_issues(
    task: dict[str, Any], branches: list[Any]
) -> list[ValidationIssue]:
    """Bind mutable branch runtime state to the immutable embedded task plan."""

    expected = _expected_branch_specs(task)
    expected_by_id = {
        branch["id"]: branch
        for branch in expected
        if isinstance(branch, dict) and isinstance(branch.get("id"), str)
    }
    actual_by_id = {
        branch["id"]: (index, branch)
        for index, branch in enumerate(branches)
        if isinstance(branch, dict) and isinstance(branch.get("id"), str)
    }
    issues: list[ValidationIssue] = []

    for branch_id in expected_by_id.keys() - actual_by_id.keys():
        issues.append(
            ValidationIssue(
                "BRANCH_SPEC_MISSING",
                "$.branches",
                f"Required task branch is missing from state: {branch_id}",
            )
        )
    for branch_id in actual_by_id.keys() - expected_by_id.keys():
        index, _ = actual_by_id[branch_id]
        issues.append(
            ValidationIssue(
                "BRANCH_SPEC_UNEXPECTED",
                f"$.branches[{index}].id",
                f"State contains a branch not declared by the task: {branch_id}",
            )
        )

    for branch_id in expected_by_id.keys() & actual_by_id.keys():
        expected_branch = expected_by_id[branch_id]
        index, actual_branch = actual_by_id[branch_id]
        for field in BRANCH_SPEC_FIELDS:
            if actual_branch.get(field) != expected_branch.get(field):
                issues.append(
                    ValidationIssue(
                        "BRANCH_SPEC_MISMATCH",
                        f"$.branches[{index}].{field}",
                        f"Branch {branch_id} field {field} must match the embedded task.",
                    )
                )
    return issues


def _coverage_state_issues(state: dict[str, Any]) -> list[ValidationIssue]:
    version = state.get("schema_version")
    task = state.get("task")
    task_map = task.get("capability_map") if isinstance(task, dict) else None
    coverage = state.get("coverage")
    branches = state.get("branches")
    branch_items = branches if isinstance(branches, list) else []
    extended = any(
        isinstance(branch, dict)
        and any(field in branch for field in COVERAGE_BRANCH_FIELDS)
        for branch in branch_items
    )

    if version == "2.0":
        if task_map is not None or coverage is not None or extended:
            return [
                ValidationIssue(
                    "STATE_VERSION_FEATURE_MISMATCH",
                    "$.schema_version",
                    "Schema 2.0 cannot contain Capability Map coverage fields.",
                )
            ]
        return []
    if version != "2.1":
        return []

    issues: list[ValidationIssue] = []
    if not isinstance(task_map, dict) or not isinstance(coverage, dict):
        issues.append(
            ValidationIssue(
                "COVERAGE_STATE_REQUIRED",
                "$.coverage",
                "Schema 2.1 requires compiled map metadata and coverage state.",
            )
        )
        return issues
    if coverage.get("policy") != task_map.get("wide_pass_policy"):
        issues.append(
            ValidationIssue(
                "COVERAGE_POLICY_MISMATCH",
                "$.coverage.policy",
                "Coverage policy must match the embedded task.",
            )
        )
    if coverage.get("map_digest") != task_map.get("source_digest"):
        issues.append(
            ValidationIssue(
                "COVERAGE_MAP_DIGEST_MISMATCH",
                "$.coverage.map_digest",
                "Coverage digest must match the embedded task.",
            )
        )

    stage = coverage.get("execution_stage")
    advanced_at = coverage.get("advanced_at")
    history = coverage.get("history")
    history_items = history if isinstance(history, list) else []
    if stage == "WIDE" and (advanced_at is not None or history_items):
        issues.append(
            ValidationIssue(
                "COVERAGE_STAGE_INVALID",
                "$.coverage",
                "WIDE coverage cannot contain a deep-transition record.",
            )
        )
    if stage == "DEEP":
        if (
            not isinstance(advanced_at, str)
            or len(history_items) != 1
            or not isinstance(history_items[0], dict)
            or history_items[0].get("timestamp") != advanced_at
        ):
            issues.append(
                ValidationIssue(
                    "COVERAGE_STAGE_INVALID",
                    "$.coverage",
                    "DEEP coverage requires exactly one matching transition record.",
                )
            )
        else:
            calculated = compute_coverage(state)
            ready = calculated["wide_pass_ready"]
            override = history_items[0].get("override")
            if coverage.get("policy") == "REQUIRED" and not ready:
                issues.append(
                    ValidationIssue(
                        "COVERAGE_STAGE_INVALID",
                        "$.coverage.execution_stage",
                        "REQUIRED coverage cannot remain DEEP after baseline evidence is lost.",
                    )
                )
            if coverage.get("policy") == "ADVISORY":
                if not ready and override is not True:
                    issues.append(
                        ValidationIssue(
                            "COVERAGE_STAGE_INVALID",
                            "$.coverage.history[0].override",
                            "Incomplete advisory coverage requires an explicit override.",
                        )
                    )
                if ready and override is not False:
                    issues.append(
                        ValidationIssue(
                            "COVERAGE_STAGE_INVALID",
                            "$.coverage.history[0].override",
                            "A completed wide pass is not an override.",
                        )
                    )
    return issues


def _branch_issues(branches: list[Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    branch_ids: list[str] = [
        branch.get("id")
        for branch in branches
        if isinstance(branch, dict) and isinstance(branch.get("id"), str)
    ]
    known_ids = set(branch_ids)

    seen: set[str] = set()
    for index, branch_id in enumerate(branch_ids):
        if branch_id in seen:
            issues.append(
                ValidationIssue(
                    "BRANCH_ID_DUPLICATE",
                    f"$.branches[{index}].id",
                    f"Duplicate branch id: {branch_id}",
                )
            )
        seen.add(branch_id)

    graph: dict[str, list[str]] = {}
    for index, branch in enumerate(branches):
        if not isinstance(branch, dict):
            continue
        branch_id = branch.get("id")
        if not isinstance(branch_id, str):
            continue

        if branch.get("kind") == "primary" and branch.get("priority") == "DEFERRED":
            issues.append(
                ValidationIssue(
                    "PRIMARY_DEFERRED",
                    f"$.branches[{index}].priority",
                    "A primary branch cannot use DEFERRED priority.",
                )
            )

        evidence = branch.get("evidence")
        if branch.get("status") == "VERIFIED" and not has_passing_completion_evidence(
            evidence
        ):
            issues.append(
                ValidationIssue(
                    "VERIFIED_EVIDENCE_REQUIRED",
                    f"$.branches[{index}].evidence",
                    "A verified branch requires passing non-baseline completion evidence.",
                )
            )
        if branch.get("status") == "BLOCKED":
            if not branch.get("blocked_reason"):
                issues.append(
                    ValidationIssue(
                        "BLOCKED_REASON_REQUIRED",
                        f"$.branches[{index}].blocked_reason",
                        "A blocked branch requires a reason.",
                    )
                )
            if not isinstance(evidence, list) or not evidence:
                issues.append(
                    ValidationIssue(
                        "BLOCKED_EVIDENCE_REQUIRED",
                        f"$.branches[{index}].evidence",
                        "A blocked branch requires evidence.",
                    )
                )

        if branch.get("status") == "ACCEPTED_LIMITATION":
            if not isinstance(branch.get("limitation"), dict):
                issues.append(
                    ValidationIssue(
                        "LIMITATION_RECORD_REQUIRED",
                        f"$.branches[{index}].limitation",
                        "An accepted limitation requires a structured record.",
                    )
                )
            if not isinstance(evidence, list) or not evidence:
                issues.append(
                    ValidationIssue(
                        "LIMITATION_EVIDENCE_REQUIRED",
                        f"$.branches[{index}].evidence",
                        "An accepted limitation requires evidence.",
                    )
                )

        dependencies = branch.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        graph[branch_id] = [item for item in dependencies if isinstance(item, str)]
        for dependency in graph[branch_id]:
            if dependency == branch_id:
                issues.append(
                    ValidationIssue(
                        "DEPENDENCY_SELF",
                        f"$.branches[{index}].depends_on",
                        f"Branch {branch_id} cannot depend on itself.",
                    )
                )
            elif dependency not in known_ids:
                issues.append(
                    ValidationIssue(
                        "DEPENDENCY_MISSING",
                        f"$.branches[{index}].depends_on",
                        f"Unknown dependency: {dependency}",
                    )
                )

    if has_cycle(graph):
        issues.append(
            ValidationIssue(
                "DEPENDENCY_CYCLE",
                "$.branches",
                "Branch dependencies must form a directed acyclic graph.",
            )
        )
    return issues

def _history_issues(state: dict[str, Any]) -> list[ValidationIssue]:
    history = state.get("history")
    if not isinstance(history, list) or not history:
        return []

    issues: list[ValidationIssue] = []
    previous_to: str | None = None
    for index, item in enumerate(history):
        if not isinstance(item, dict):
            continue
        current_from = item.get("from")
        current_to = item.get("to")
        expected_from = None if index == 0 else previous_to
        if current_from != expected_from:
            issues.append(
                ValidationIssue(
                    "HISTORY_CHAIN_INVALID",
                    f"$.history[{index}].from",
                    f"History transition must start from {expected_from!r}.",
                )
            )
        if index == 0:
            if current_to != PHASES[0]:
                issues.append(
                    ValidationIssue(
                        "HISTORY_INITIAL_PHASE_INVALID",
                        "$.history[0].to",
                        f"History must begin at {PHASES[0]}.",
                    )
                )
        elif previous_to in PHASES:
            expected_index = PHASES.index(previous_to) + 1
            expected_to = PHASES[expected_index] if expected_index < len(PHASES) else None
            if current_to != expected_to:
                issues.append(
                    ValidationIssue(
                        "HISTORY_TRANSITION_INVALID",
                        f"$.history[{index}].to",
                        f"Expected next phase {expected_to!r}.",
                    )
                )
        previous_to = current_to if isinstance(current_to, str) else None

    if previous_to != state.get("phase"):
        issues.append(
            ValidationIssue(
                "HISTORY_PHASE_MISMATCH",
                "$.history",
                "The final history target must equal the current phase.",
            )
        )
    return issues


def _phase_gate_issues(
    state: dict[str, Any], branches: list[Any]
) -> list[ValidationIssue]:
    phase = state.get("phase")
    if phase not in PHASES:
        return []
    primary = [
        branch
        for branch in branches
        if isinstance(branch, dict) and branch.get("kind") == "primary"
    ]
    primary_terminal = all(
        branch.get("status") in TERMINAL_BRANCH_STATUSES for branch in primary
    )
    evidence = state.get("evidence")
    evidence_records = evidence if isinstance(evidence, list) else []
    integration_pass = _has_passing_evidence(evidence_records, "integration")
    final_pass = _has_passing_evidence(evidence_records, "final-verification")

    issues: list[ValidationIssue] = []
    if PHASES.index(phase) >= PHASES.index("integration") and not primary_terminal:
        issues.append(
            ValidationIssue(
                "PHASE_BRANCH_GATE_UNSATISFIED",
                "$.phase",
                "Integration and later phases require terminal primary branches.",
            )
        )
    if PHASES.index(phase) >= PHASES.index("verification") and not integration_pass:
        issues.append(
            ValidationIssue(
                "PHASE_INTEGRATION_EVIDENCE_REQUIRED",
                "$.evidence",
                "Verification and completion require passing integration evidence.",
            )
        )
    if phase == "complete" and not final_pass:
        issues.append(
            ValidationIssue(
                "PHASE_FINAL_EVIDENCE_REQUIRED",
                "$.evidence",
                "Complete phase requires passing final-verification evidence.",
            )
        )
    return issues


def _has_passing_evidence(evidence: list[Any], evidence_type: str) -> bool:
    return any(
        isinstance(item, dict)
        and item.get("type") == evidence_type
        and item.get("outcome") == "PASS"
        for item in evidence
    )


def has_passing_completion_evidence(evidence: object) -> bool:
    """Return whether branch evidence proves completion rather than baseline presence."""

    return isinstance(evidence, list) and any(
        isinstance(item, dict)
        and item.get("outcome") == "PASS"
        and item.get("type") != "baseline"
        for item in evidence
    )


def _deduplicate(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    output: list[ValidationIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            output.append(issue)
            seen.add(key)
    return output
