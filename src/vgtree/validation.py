"""Strict structural and semantic validation for VGTREE documents."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from vgtree.models import ValidationIssue, ValidationReport


def _load_schema(name: str) -> dict[str, Any]:
    schema_path = files("vgtree").joinpath("schemas", name)
    return json.loads(schema_path.read_text(encoding="utf-8"))


TASK_SCHEMA = _load_schema("task.schema.json")
STATE_SCHEMA = _load_schema("state.schema.json")
TASK_VALIDATOR = Draft202012Validator(TASK_SCHEMA)
STATE_VALIDATOR = Draft202012Validator(STATE_SCHEMA)
EVIDENCE_VALIDATOR = Draft202012Validator(
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "#/$defs/evidence",
        "$defs": STATE_SCHEMA["$defs"],
    }
)


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
    for issue in validate_task(task).issues:
        issues.append(
            ValidationIssue(issue.code, f"$.task{issue.path[1:]}", issue.message)
        )

    branches = state.get("branches")
    if not isinstance(branches, list):
        return _report(issues)

    issues.extend(_branch_issues(branches))
    return _report(_deduplicate(issues))


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

    if _has_cycle(graph):
        issues.append(
            ValidationIssue(
                "DEPENDENCY_CYCLE",
                "$.branches",
                "Branch dependencies must form a directed acyclic graph.",
            )
        )
    return issues


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dependency in graph.get(node, []):
            if dependency in graph and visit(dependency):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph if node not in visited)


def _deduplicate(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    output: list[ValidationIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            output.append(issue)
            seen.add(key)
    return output
