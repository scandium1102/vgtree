"""Deterministic task classification and workflow routing."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

from vgtree.models import Decision
from vgtree.semantics import compute_task_class
from vgtree.validation import validate_task


TREE_WORKFLOW_REF = "WF-VEGA-TREE@1.0"
SPECIALIZED_MATCH_FLAGS = (
    "registered",
    "trigger_match",
    "context_match",
    "capability_match",
    "outcome_match",
    "safety_match",
)


def classify_task(
    task: dict[str, Any],
    *,
    registered_workflows: Collection[str] = (),
) -> Decision:
    report = validate_task(task)
    if not report.valid:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in report.issues)
        raise ValueError(f"Invalid task specification: {details}")

    task_class, computed_reasons = compute_task_class(task)
    reasons = list(computed_reasons)
    match = task.get("specialized_match")
    if _is_verified_specialized_match(match, registered_workflows):
        workflow_ref = match["workflow_ref"]
        return Decision(
            task_class=task_class,
            route="specialized",
            workflow_ref=workflow_ref,
            reasons=tuple([*reasons, f"verified specialized match: {workflow_ref}"]),
        )

    route = "direct" if task_class in {"T0", "T1"} else "tree"
    if match:
        reasons.append("specialized match was incomplete or not registry-verified")
    if route == "tree":
        reasons.append(f"{task_class} uses Tree execution")
    else:
        reasons.append(f"{task_class} remains direct")
    return Decision(
        task_class=task_class,
        route=route,
        workflow_ref=None,
        reasons=tuple(reasons),
    )

def _is_verified_specialized_match(
    match: Any, registered_workflows: Collection[str]
) -> bool:
    if not isinstance(match, dict):
        return False
    workflow_ref = match.get("workflow_ref")
    return (
        isinstance(workflow_ref, str)
        and workflow_ref in registered_workflows
        and all(match.get(flag) is True for flag in SPECIALIZED_MATCH_FLAGS)
    )
