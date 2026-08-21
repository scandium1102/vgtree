"""Pure breadth-coverage calculation shared by validation and execution."""

from __future__ import annotations

from typing import Any


def compute_coverage(state: dict[str, Any]) -> dict[str, Any]:
    """Compute exact baseline coverage without mutating or validating state."""

    coverage = state.get("coverage")
    policy = coverage.get("policy") if isinstance(coverage, dict) else "OFF"
    execution_stage = (
        coverage.get("execution_stage") if isinstance(coverage, dict) else None
    )
    required: list[str] = []
    covered: list[str] = []
    missing: dict[str, list[str]] = {}

    branches = state.get("branches")
    branch_items = branches if isinstance(branches, list) else []
    for branch in branch_items:
        if not isinstance(branch, dict) or branch.get("coverage_required") is not True:
            continue
        branch_id = branch.get("id")
        if not isinstance(branch_id, str):
            continue
        required.append(branch_id)
        declared = {
            item
            for item in branch.get("baseline_evidence_requirements", [])
            if isinstance(item, str)
        }
        observed = {
            item.get("method")
            for item in branch.get("evidence", [])
            if isinstance(item, dict)
            and item.get("type") == "baseline"
            and item.get("outcome") == "PASS"
            and item.get("subject") == f"branch:{branch_id}:baseline"
            and isinstance(item.get("method"), str)
        }
        outstanding = sorted(declared - observed)
        if outstanding:
            missing[branch_id] = outstanding
        else:
            covered.append(branch_id)

    required.sort()
    covered.sort()
    missing_branches = sorted(missing)
    ratio = len(covered) / len(required) if required else 1.0
    return {
        "policy": policy,
        "execution_stage": execution_stage,
        "required_branches": required,
        "covered_branches": covered,
        "missing_branches": missing_branches,
        "missing_requirements": {
            branch_id: missing[branch_id] for branch_id in missing_branches
        },
        "coverage_ratio": ratio,
        "wide_pass_ready": not missing_branches,
    }
