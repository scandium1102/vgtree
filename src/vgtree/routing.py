"""Deterministic task classification and workflow routing."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

from vgtree.models import Decision
from vgtree.validation import validate_task


TREE_WORKFLOW_REF = "WF-VEGA-TREE@1.0"
TASK_CLASS_RANK = {"T0": 0, "T1": 1, "T2": 2, "T3": 3, "T4": 4}
TASK_CLASS_BY_RANK = {rank: name for name, rank in TASK_CLASS_RANK.items()}
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

    signals = task["signals"]
    minimum_rank, reasons = _minimum_rank(signals)
    explicit = task.get("explicit_class")
    final_rank = max(minimum_rank, TASK_CLASS_RANK.get(explicit, 0))
    if explicit and TASK_CLASS_RANK[explicit] > minimum_rank:
        reasons.append(f"explicit upgrade to {explicit}")
    elif explicit and TASK_CLASS_RANK[explicit] < minimum_rank:
        reasons.append(f"explicit {explicit} ignored below computed minimum")

    task_class = TASK_CLASS_BY_RANK[final_rank]
    match = task.get("specialized_match")
    if _is_verified_specialized_match(match, registered_workflows):
        workflow_ref = match["workflow_ref"]
        return Decision(
            task_class=task_class,
            route="specialized",
            workflow_ref=workflow_ref,
            reasons=tuple([*reasons, f"verified specialized match: {workflow_ref}"]),
        )

    route = "direct" if final_rank <= TASK_CLASS_RANK["T1"] else "tree"
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


def _minimum_rank(signals: dict[str, Any]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    estimated_files = signals["estimated_files"]
    if estimated_files >= 10:
        rank = TASK_CLASS_RANK["T3"]
        reasons.append("ten or more estimated files")
    elif estimated_files >= 3:
        rank = TASK_CLASS_RANK["T2"]
        reasons.append("multi-file integration")
    elif estimated_files >= 2:
        rank = TASK_CLASS_RANK["T1"]
        reasons.append("small bounded multi-step work")
    else:
        rank = TASK_CLASS_RANK["T0"]
        reasons.append("single-surface low-complexity work")

    t3_signals = {
        "migration": "migration",
        "project_scale": "project-scale change",
        "external_effect": "external effect",
        "cross_system": "cross-system change",
    }
    for key, reason in t3_signals.items():
        if signals[key]:
            rank = max(rank, TASK_CLASS_RANK["T3"])
            reasons.append(reason)

    for key in ("destructive", "irreversible"):
        if signals[key]:
            rank = TASK_CLASS_RANK["T4"]
            reasons.append(key.replace("_", " "))
    return rank, reasons


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
