"""Shared derived task semantics without validation import cycles."""

from __future__ import annotations

from typing import Any


TASK_CLASS_RANK = {"T0": 0, "T1": 1, "T2": 2, "T3": 3, "T4": 4}
TASK_CLASS_BY_RANK = {rank: name for name, rank in TASK_CLASS_RANK.items()}


def compute_task_class(task: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    signals = task["signals"]
    minimum_rank, reasons = _minimum_rank(signals)
    explicit = task.get("explicit_class")
    final_rank = max(minimum_rank, TASK_CLASS_RANK.get(explicit, 0))
    if explicit and TASK_CLASS_RANK[explicit] > minimum_rank:
        reasons.append(f"explicit upgrade to {explicit}")
    elif explicit and TASK_CLASS_RANK[explicit] < minimum_rank:
        reasons.append(f"explicit {explicit} ignored below computed minimum")
    return TASK_CLASS_BY_RANK[final_rank], tuple(reasons)


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

    for key, reason in {
        "migration": "migration",
        "project_scale": "project-scale change",
        "external_effect": "external effect",
        "cross_system": "cross-system change",
    }.items():
        if signals[key]:
            rank = max(rank, TASK_CLASS_RANK["T3"])
            reasons.append(reason)

    for key in ("destructive", "irreversible"):
        if signals[key]:
            rank = TASK_CLASS_RANK["T4"]
            reasons.append(key.replace("_", " "))
    return rank, reasons
