"""Validate deterministic VGTREE v1.1 evaluation fixtures."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "evals" / "v1.1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
FAMILIES = {"website", "vision", "research", "ros-observer", "agent-runtime"}
EXPECTED_CODES = {
    "ACCEPTANCE_MODULE_UNKNOWN",
    "CAPABILITY_DEPENDENCY_CYCLE",
    "CAPABILITY_ID_DUPLICATE",
    "CONSTRAINT_ORDER_UNENFORCED",
    "COVERAGE_REQUIRED_MODULE_MISSING",
}
MANIFEST_KEYS = {
    "fixture_version",
    "family",
    "request",
    "golden_capabilities",
    "required_interfaces",
    "invalid_cases",
    "expected_coverage",
}


def validate_manifest(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["manifest must be an object"]
    _exact_keys(value, MANIFEST_KEYS, "manifest", errors)
    if value.get("fixture_version") != "1.0":
        errors.append("fixture_version must be 1.0")
    family = value.get("family")
    if family not in FAMILIES:
        errors.append("family is invalid")
    if not _nonempty(value.get("request")):
        errors.append("request must be non-empty")
    capabilities = _safe_unique_list(
        value.get("golden_capabilities"), "golden_capabilities", errors
    )
    if not capabilities:
        errors.append("golden_capabilities must not be empty")
    _safe_unique_list(value.get("required_interfaces"), "required_interfaces", errors)
    if family == "ros-observer" and any(
        item == "cmd-vel" or "control-mutation" in item for item in capabilities
    ):
        errors.append("ros-observer cannot contain control capabilities")

    invalid_cases = value.get("invalid_cases")
    if not isinstance(invalid_cases, list) or not invalid_cases:
        errors.append("invalid_cases must be a non-empty array")
    else:
        seen: set[str] = set()
        for index, case in enumerate(invalid_cases):
            if not isinstance(case, dict):
                errors.append(f"invalid_cases[{index}] must be an object")
                continue
            _exact_keys(case, {"id", "expected_code"}, f"invalid_cases[{index}]", errors)
            case_id = case.get("id")
            if not isinstance(case_id, str) or not SAFE_ID.fullmatch(case_id):
                errors.append(f"invalid_cases[{index}].id is unsafe")
            elif case_id in seen:
                errors.append(f"invalid_cases[{index}].id is duplicated")
            seen.add(case_id) if isinstance(case_id, str) else None
            if case.get("expected_code") not in EXPECTED_CODES:
                errors.append(f"invalid_cases[{index}].expected_code is invalid")

    expected = value.get("expected_coverage")
    if not isinstance(expected, dict):
        errors.append("expected_coverage must be an object")
    else:
        _exact_keys(
            expected,
            {
                "required",
                "wide_pass_ready_before_evidence",
                "wide_pass_ready_after_evidence",
            },
            "expected_coverage",
            errors,
        )
        if expected.get("required") != len(capabilities):
            errors.append("expected_coverage.required must equal golden capabilities")
        if expected.get("wide_pass_ready_before_evidence") is not False:
            errors.append("wide pass must not be ready before evidence")
        if expected.get("wide_pass_ready_after_evidence") is not True:
            errors.append("wide pass must be ready after evidence")
    return errors


def validate_context_budget(
    catalog: object, selection: object
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    tools: list[dict[str, Any]] = []
    if not isinstance(catalog, dict) or set(catalog) != {"tools"}:
        errors.append("catalog must contain only tools")
    elif not isinstance(catalog["tools"], list):
        errors.append("catalog.tools must be an array")
    else:
        tools = catalog["tools"]
    names: list[str] = []
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict) or set(tool) != {
            "name",
            "description",
            "input_schema",
        }:
            errors.append(f"catalog.tools[{index}] has an invalid shape")
            continue
        name = tool.get("name")
        if not isinstance(name, str) or not SAFE_ID.fullmatch(name):
            errors.append(f"catalog.tools[{index}].name is unsafe")
        else:
            names.append(name)
        if not _nonempty(tool.get("description")) or not isinstance(
            tool.get("input_schema"), dict
        ):
            errors.append(f"catalog.tools[{index}] metadata is invalid")
    if len(names) != len(set(names)):
        errors.append("catalog tool names must be unique")

    selection_keys = {
        "primary_skill",
        "support_skills",
        "override_reason",
        "unload_condition",
        "inspected_tools",
        "invoked_tools",
    }
    if not isinstance(selection, dict):
        errors.append("selection must be an object")
        selection = {}
    else:
        _exact_keys(selection, selection_keys, "selection", errors)
    primary = selection.get("primary_skill")
    support = selection.get("support_skills")
    support_items = support if isinstance(support, list) else []
    if not _nonempty(primary):
        errors.append("primary_skill is required")
    if not isinstance(support, list) or any(not _nonempty(item) for item in support):
        errors.append("support_skills must be a string array")
    active_count = (1 if _nonempty(primary) else 0) + len(support_items)
    override = selection.get("override_reason")
    if active_count > 2 and not _nonempty(override):
        errors.append("override_reason is required above two active bundles")
    if not _nonempty(selection.get("unload_condition")):
        errors.append("unload_condition is required")

    inspected = selection.get("inspected_tools")
    invoked = selection.get("invoked_tools")
    inspected_items = inspected if isinstance(inspected, list) else []
    invoked_items = invoked if isinstance(invoked, list) else []
    if not isinstance(inspected, list) or any(item not in names for item in inspected_items):
        errors.append("inspected_tools must reference catalog tools")
    if not isinstance(invoked, list) or any(item not in inspected_items for item in invoked_items):
        errors.append("invoked_tools must be a subset of inspected_tools")
    inspected_records = [tool for tool in tools if tool.get("name") in inspected_items]
    metrics = {
        "active_bundle_count": active_count,
        "full_catalog_count": len(tools),
        "full_catalog_serialized_bytes": len(_serialized(catalog)),
        "inspected_tool_count": len(inspected_items),
        "inspected_tool_serialized_bytes": len(_serialized(inspected_records)),
        "unnecessary_inspections": sorted(set(inspected_items) - set(invoked_items)),
        "override_reason_required": active_count > 2,
    }
    return errors, metrics


def validate_behavioral_result(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["behavioral result must be an object"]
    required = {
        "result_version",
        "fixture_family",
        "fixture_digest",
        "run_date",
        "provider",
        "model",
        "tool_availability",
        "trial_count",
        "baseline",
        "candidate",
        "artifact_references",
        "claim_scope",
    }
    _exact_keys(value, required, "result", errors)
    if value.get("result_version") != "1.0":
        errors.append("result_version must be 1.0")
    if value.get("fixture_family") not in FAMILIES:
        errors.append("fixture_family is invalid")
    if not isinstance(value.get("fixture_digest"), str) or not SHA256.fullmatch(
        value["fixture_digest"]
    ):
        errors.append("fixture_digest must be lowercase SHA-256")
    if not isinstance(value.get("run_date"), str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", value["run_date"]
    ):
        errors.append("run_date must be YYYY-MM-DD")
    if not _nonempty(value.get("provider")):
        errors.append("provider is required")
    model = value.get("model")
    if not isinstance(model, dict):
        errors.append("model is required")
    else:
        _exact_keys(model, {"selector", "reasoning"}, "model", errors)
        for field in ("selector", "reasoning"):
            if not _nonempty(model.get(field)):
                errors.append(f"model.{field} is required")
    tools = value.get("tool_availability")
    if not isinstance(tools, list) or not tools or any(not _nonempty(item) for item in tools):
        errors.append("tool_availability must be a non-empty string array")
    trials = value.get("trial_count")
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 1:
        errors.append("trial_count must be at least one")
    for field in ("baseline", "candidate"):
        errors.extend(_metric_errors(value.get(field), field))
    artifacts = value.get("artifact_references")
    if not isinstance(artifacts, list) or not artifacts or any(
        not _nonempty(item) for item in artifacts
    ):
        errors.append("artifact_references must be non-empty")
    claim = value.get("claim_scope")
    if not _nonempty(claim) or not (
        "not a measured" in claim.lower() or "environment" in claim.lower()
    ):
        errors.append("claim_scope must state measurement or environment limits")
    return errors


def _metric_errors(value: object, path: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{path} metrics are required"]
    keys = {
        "capability_recall",
        "invalid_dependencies",
        "premature_deep_attempts",
        "unsupported_completion_claims",
    }
    errors: list[str] = []
    _exact_keys(value, keys, path, errors)
    recall = value.get("capability_recall")
    if not isinstance(recall, (int, float)) or isinstance(recall, bool) or not 0 <= recall <= 1:
        errors.append(f"{path}.capability_recall must be between zero and one")
    for key in keys - {"capability_recall"}:
        metric = value.get(key)
        if not isinstance(metric, int) or isinstance(metric, bool) or metric < 0:
            errors.append(f"{path}.{key} must be a non-negative integer")
    return errors


def _exact_keys(
    value: dict[str, Any], expected: set[str], path: str, errors: list[str]
) -> None:
    for key in sorted(expected - set(value)):
        errors.append(f"{path}.{key} is required")
    for key in sorted(set(value) - expected):
        errors.append(f"{path}.{key} is not allowed")


def _safe_unique_list(value: object, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return []
    output: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not SAFE_ID.fullmatch(item):
            errors.append(f"{path}[{index}] is unsafe")
        else:
            output.append(item)
    if len(output) != len(set(output)):
        errors.append(f"{path} must be unique")
    return output


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _serialized(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def main() -> int:
    errors: list[str] = []
    manifests = sorted(EVAL_ROOT.glob("*/manifest.json"))
    for path in manifests:
        for error in validate_manifest(json.loads(path.read_text(encoding="utf-8"))):
            errors.append(f"{path.relative_to(ROOT)}: {error}")
    catalog = json.loads(
        (EVAL_ROOT / "context-budget" / "catalog.json").read_text(encoding="utf-8")
    )
    selection = json.loads(
        (EVAL_ROOT / "context-budget" / "selection.json").read_text(encoding="utf-8")
    )
    context_errors, context_metrics = validate_context_budget(catalog, selection)
    errors.extend(f"context-budget: {error}" for error in context_errors)
    example = json.loads(
        (EVAL_ROOT / "behavioral-result.example.json").read_text(encoding="utf-8")
    )
    errors.extend(
        f"behavioral-result.example.json: {error}"
        for error in validate_behavioral_result(example)
    )
    result_paths = sorted((EVAL_ROOT / "results").glob("*.json"))
    for path in result_paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(
            f"{path.relative_to(ROOT)}: {error}"
            for error in validate_behavioral_result(value)
        )
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "manifest_count": len(manifests),
        "context_budget": context_metrics,
        "behavioral_example": "shape-only",
        "measured_behavioral_results": len(result_paths),
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
