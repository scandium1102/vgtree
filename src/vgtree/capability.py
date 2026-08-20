"""Capability Map validation, deterministic compilation, and bounded loading."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from vgtree.dag import has_cycle
from vgtree.models import GuardResult, ValidationIssue, ValidationReport


MAX_CAPABILITY_MAP_BYTES = 4 * 1024 * 1024
SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
CAPABILITY_MAP_SCHEMA = json.loads(
    files("vgtree")
    .joinpath("schemas", "capability-map.schema.json")
    .read_text(encoding="utf-8")
)
CAPABILITY_MAP_VALIDATOR = Draft202012Validator(CAPABILITY_MAP_SCHEMA)


def _json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _schema_issues(value: object) -> list[ValidationIssue]:
    return [
        ValidationIssue("SCHEMA_INVALID", _json_path(error.absolute_path), error.message)
        for error in sorted(
            CAPABILITY_MAP_VALIDATOR.iter_errors(value),
            key=lambda item: list(item.absolute_path),
        )
    ]


def _deduplicate(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    output: list[ValidationIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            output.append(issue)
            seen.add(key)
    return output


def validate_capability_map(value: object) -> ValidationReport:
    """Validate a Capability Map structurally and semantically."""

    issues = _schema_issues(value)
    if isinstance(value, dict) and not issues:
        issues.extend(_semantic_issues(value))
    deduplicated = tuple(_deduplicate(issues))
    return ValidationReport("PASS" if not deduplicated else "FAIL", deduplicated)


def _semantic_issues(value: dict[str, Any]) -> list[ValidationIssue]:
    modules: list[dict[str, Any]] = value["modules"]
    module_by_id: dict[str, dict[str, Any]] = {}
    issues: list[ValidationIssue] = []

    for index, module in enumerate(modules):
        module_id = module["id"]
        if module_id in module_by_id:
            issues.append(
                ValidationIssue(
                    "CAPABILITY_ID_DUPLICATE",
                    f"$.modules[{index}].id",
                    f"Duplicate capability module id: {module_id}",
                )
            )
        else:
            module_by_id[module_id] = module

        if module["kind"] == "primary" and module["priority"] == "DEFERRED":
            issues.append(
                ValidationIssue(
                    "PRIMARY_DEFERRED",
                    f"$.modules[{index}].priority",
                    "A primary module cannot use DEFERRED priority.",
                )
            )
        if module["coverage_required"] and (
            not module["minimum_viable_state"]
            or not module["baseline_evidence_requirements"]
        ):
            issues.append(
                ValidationIssue(
                    "COVERAGE_BASELINE_REQUIRED",
                    f"$.modules[{index}]",
                    "Coverage-required modules need a viable state and baseline evidence requirement.",
                )
            )
        if module["priority"] != "DEFERRED" and (
            not module["definition_of_done"]
            or not module["acceptance_evidence"]
            or not module["stop_condition"].strip()
        ):
            issues.append(
                ValidationIssue(
                    "COMPLETION_REQUIREMENTS_MISSING",
                    f"$.modules[{index}]",
                    "Non-deferred modules require completion, evidence, and stop conditions.",
                )
            )

    if value["wide_pass_policy"] in {"ADVISORY", "REQUIRED"} and not any(
        module["coverage_required"] for module in modules
    ):
        issues.append(
            ValidationIssue(
                "COVERAGE_REQUIRED_MODULE_MISSING",
                "$.modules",
                "An opted-in map requires at least one coverage-required module.",
            )
        )

    graph: dict[str, list[str]] = {}
    known_ids = set(module_by_id)
    for index, module in enumerate(modules):
        module_id = module["id"]
        graph[module_id] = list(module["depends_on"])
        for dependency in module["depends_on"]:
            if dependency == module_id:
                issues.append(
                    ValidationIssue(
                        "CAPABILITY_DEPENDENCY_SELF",
                        f"$.modules[{index}].depends_on",
                        f"Module {module_id} cannot depend on itself.",
                    )
                )
            elif dependency not in known_ids:
                issues.append(
                    ValidationIssue(
                        "CAPABILITY_DEPENDENCY_MISSING",
                        f"$.modules[{index}].depends_on",
                        f"Unknown dependency: {dependency}",
                    )
                )
    if has_cycle(graph):
        issues.append(
            ValidationIssue(
                "CAPABILITY_DEPENDENCY_CYCLE",
                "$.modules",
                "Capability dependencies must form a directed acyclic graph.",
            )
        )

    constraints: list[dict[str, Any]] = value["cross_cutting_constraints"]
    acceptance: list[dict[str, Any]] = value["final_acceptance_matrix"]
    issues.extend(_unique_record_id_issues(constraints, "cross_cutting_constraints"))
    issues.extend(_unique_record_id_issues(acceptance, "final_acceptance_matrix"))

    for index, constraint in enumerate(constraints):
        owner_id = constraint["owner_branch_id"]
        owner = module_by_id.get(owner_id)
        if owner is None:
            issues.append(
                ValidationIssue(
                    "CONSTRAINT_OWNER_UNKNOWN",
                    f"$.cross_cutting_constraints[{index}].owner_branch_id",
                    f"Unknown constraint owner: {owner_id}",
                )
            )
        for module_id in constraint["module_ids"]:
            if module_id not in known_ids:
                issues.append(
                    ValidationIssue(
                        "CONSTRAINT_MODULE_UNKNOWN",
                        f"$.cross_cutting_constraints[{index}].module_ids",
                        f"Unknown constrained module: {module_id}",
                    )
                )
        if constraint["gate"] == "PRE_EXECUTION" and owner is not None:
            ordered = owner["kind"] == "primary" and owner["priority"] == "P0"
            ordered = ordered and all(
                module_id == owner_id
                or owner_id in module_by_id.get(module_id, {}).get("depends_on", [])
                for module_id in constraint["module_ids"]
            )
            if not ordered:
                issues.append(
                    ValidationIssue(
                        "CONSTRAINT_ORDER_UNENFORCED",
                        f"$.cross_cutting_constraints[{index}]",
                        "PRE_EXECUTION constraints require a primary P0 owner and dependency edges.",
                    )
                )
        if (
            constraint["gate"] == "COVERAGE"
            and owner is not None
            and not owner["coverage_required"]
        ):
            issues.append(
                ValidationIssue(
                    "COVERAGE_BASELINE_REQUIRED",
                    f"$.cross_cutting_constraints[{index}].owner_branch_id",
                    "COVERAGE constraints require a coverage-required owner.",
                )
            )
        if constraint["gate"] == "COMPLETION":
            affected = set(constraint["module_ids"])
            if not any(affected.issubset(set(row["module_ids"])) for row in acceptance):
                issues.append(
                    ValidationIssue(
                        "COMPLETION_CONSTRAINT_UNMAPPED",
                        f"$.cross_cutting_constraints[{index}]",
                        "COMPLETION constraints must be represented in an acceptance row.",
                    )
                )

    for index, row in enumerate(acceptance):
        row_modules = [module_by_id.get(module_id) for module_id in row["module_ids"]]
        if any(module is None for module in row_modules):
            issues.append(
                ValidationIssue(
                    "ACCEPTANCE_MODULE_UNKNOWN",
                    f"$.final_acceptance_matrix[{index}].module_ids",
                    "Acceptance rows cannot reference unknown modules.",
                )
            )
        known_modules = [module for module in row_modules if module is not None]
        if known_modules and all(
            module["priority"] == "DEFERRED" for module in known_modules
        ):
            issues.append(
                ValidationIssue(
                    "ACCEPTANCE_DEFERRED_ONLY",
                    f"$.final_acceptance_matrix[{index}].module_ids",
                    "Acceptance rows cannot contain only deferred modules.",
                )
            )
    return issues


def _unique_record_id_issues(
    records: list[dict[str, Any]], field: str
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        record_id = record["id"]
        if record_id in seen:
            issues.append(
                ValidationIssue(
                    "CAPABILITY_ID_DUPLICATE",
                    f"$.{field}[{index}].id",
                    f"Duplicate record id: {record_id}",
                )
            )
        seen.add(record_id)
    return issues


def compile_capability_map(
    value: dict[str, Any], *, source_digest: str
) -> GuardResult:
    """Compile a valid map into the immutable task contract."""

    report = validate_capability_map(value)
    if not report.valid:
        return GuardResult(
            "FAIL",
            "CAPABILITY_MAP_INVALID",
            "Capability Map failed validation.",
            {"validation": report.as_dict()},
        )
    if not SHA256_PATTERN.fullmatch(source_digest):
        return GuardResult(
            "FAIL",
            "CAPABILITY_SOURCE_DIGEST_INVALID",
            "source_digest must be a lowercase SHA-256 digest.",
        )

    policy = value["wide_pass_policy"]
    task: dict[str, Any] = {
        "task_id": value["task_id"],
        "title": value["title"],
        "description": value.get("description", value["goal"]),
        "signals": copy.deepcopy(value["signals"]),
        "branches": [_compile_branch(module, policy) for module in value["modules"]],
    }
    for optional in ("explicit_class", "specialized_match"):
        if optional in value:
            task[optional] = copy.deepcopy(value[optional])
    if policy != "OFF":
        task["capability_map"] = {
            "map_version": value["map_version"],
            "source_digest": source_digest,
            "wide_pass_policy": policy,
            "cross_cutting_constraints": copy.deepcopy(
                value["cross_cutting_constraints"]
            ),
            "final_acceptance_matrix": copy.deepcopy(
                value["final_acceptance_matrix"]
            ),
        }
    return GuardResult(
        "PASS",
        "CAPABILITY_MAP_COMPILED",
        "Capability Map compiled into a task specification.",
        {"task": task, "warnings": _interface_warnings(value)},
    )


def _compile_branch(module: dict[str, Any], policy: str) -> dict[str, Any]:
    branch = {
        "id": module["id"],
        "title": module["title"],
        "kind": module["kind"],
        "priority": module["priority"],
        "depends_on": copy.deepcopy(module["depends_on"]),
        "definition_of_done": copy.deepcopy(module["definition_of_done"]),
        "evidence_requirements": copy.deepcopy(module["acceptance_evidence"]),
        "stop_condition": module["stop_condition"],
    }
    if policy != "OFF":
        for field in (
            "coverage_required",
            "minimum_viable_state",
            "baseline_evidence_requirements",
            "shared_interfaces",
            "deferred_details",
        ):
            branch[field] = copy.deepcopy(module[field])
    return branch


def _interface_warnings(value: dict[str, Any]) -> list[str]:
    modules: list[dict[str, Any]] = value["modules"]
    constraints: list[dict[str, Any]] = value["cross_cutting_constraints"]
    usage: dict[str, list[str]] = {}
    for module in modules:
        for interface in module["shared_interfaces"]:
            usage.setdefault(interface, []).append(module["id"])
    constrained_ids = {
        module_id
        for constraint in constraints
        for module_id in [constraint["owner_branch_id"], *constraint["module_ids"]]
    }
    warnings = []
    for interface, module_ids in sorted(usage.items()):
        if len(set(module_ids)) < 2 and not set(module_ids).issubset(constrained_ids):
            warnings.append(
                f"Shared interface {interface!r} is declared by only one unconstrained module."
            )
    return warnings


def load_capability_map(
    path: Path, *, max_bytes: int = MAX_CAPABILITY_MAP_BYTES
) -> tuple[dict[str, Any], str] | GuardResult:
    """Read one bounded map file and bind the parsed value to its exact bytes."""

    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return GuardResult("FAIL", "CAPABILITY_MAP_NOT_FOUND", "Capability Map was not found.")
    except OSError:
        return GuardResult("FAIL", "CAPABILITY_MAP_READ_FAILED", "Capability Map could not be read.")
    if len(raw) > max_bytes:
        return GuardResult(
            "FAIL", "CAPABILITY_MAP_TOO_LARGE", "Capability Map exceeds 4 MiB."
        )
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        return GuardResult(
            "FAIL", "CAPABILITY_MAP_ENCODING_INVALID", "Capability Map must be UTF-8."
        )
    try:
        value = json.loads(decoded)
    except json.JSONDecodeError:
        return GuardResult(
            "FAIL", "CAPABILITY_MAP_JSON_INVALID", "Capability Map is not valid JSON."
        )
    if not isinstance(value, dict):
        return GuardResult(
            "FAIL", "CAPABILITY_MAP_INVALID", "Capability Map must be a JSON object."
        )
    return value, digest
