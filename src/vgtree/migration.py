"""Migration from the internal VEGA Tree 1.1 state to public VGTREE 2.0."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vgtree import __version__
from vgtree.models import GuardResult
from vgtree.routing import TREE_WORKFLOW_REF
from vgtree.semantics import compute_task_class
from vgtree.store import StateStore
from vgtree.validation import validate_state


PHASE_MAP = {
    "mission_understanding": "mission_understanding",
    "classification_and_routing": "outcome_definition",
    "tree_map_and_critical_path": "breadth_mapping",
    "skeleton_pass": "branch_execution",
    "breadth_pass": "branch_execution",
    "integration_pass": "integration",
    "hardening_and_polish": "verification",
    "verification_and_completion": "verification",
    "stop_or_handoff": "verification",
}
PRIORITY_MAP = {
    "BLOCKING": "P0",
    "IMPORTANT": "P1",
    "SECONDARY": "P2",
    "DEFERRED": "DEFERRED",
}
STATUS_MAP = {
    "missing": "PENDING",
    "skeleton": "IN_PROGRESS",
    "usable": "IN_PROGRESS",
    "integrated": "IN_PROGRESS",
    "verified": "IN_PROGRESS",
    "blocked": "BLOCKED",
}


def migrate_state(
    legacy: Any, *, migrated_at: str | None = None
) -> GuardResult:
    if not isinstance(legacy, dict) or legacy.get("schema_version") != "1.1":
        return GuardResult(
            "FAIL",
            "MIGRATION_VERSION_UNSUPPORTED",
            "Only VEGA Tree state schema 1.1 can be migrated.",
        )
    required = ("mission", "primary_branches", "task_class", "phase")
    missing = [field for field in required if field not in legacy]
    if missing:
        return GuardResult(
            "FAIL",
            "MIGRATION_INPUT_INVALID",
            "Legacy state is missing required fields.",
            {"missing": missing},
        )

    timestamp = migrated_at or _timestamp()
    digest = hashlib.sha256(
        json.dumps(legacy, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    mission = legacy["mission"]
    if not isinstance(mission, dict) or not mission.get("objective"):
        return GuardResult(
            "FAIL", "MIGRATION_INPUT_INVALID", "Legacy mission is invalid."
        )

    primary = legacy.get("primary_branches")
    cross_cutting = legacy.get("cross_cutting", [])
    deferred = legacy.get("deferred", [])
    if not isinstance(primary, list) or not isinstance(cross_cutting, list):
        return GuardResult(
            "FAIL", "MIGRATION_INPUT_INVALID", "Legacy branches must be arrays."
        )

    branches: list[dict[str, Any]] = []
    for item in primary:
        converted = _migrate_branch(item, "primary", timestamp)
        if converted is None:
            return GuardResult(
                "FAIL", "MIGRATION_INPUT_INVALID", "A legacy primary branch is invalid."
            )
        branches.append(converted)
    for item in cross_cutting:
        converted = _migrate_branch(item, "secondary", timestamp)
        if converted is None:
            return GuardResult(
                "FAIL", "MIGRATION_INPUT_INVALID", "A legacy cross-cutting branch is invalid."
            )
        branches.append(converted)
    if isinstance(deferred, list):
        for index, item in enumerate(deferred, start=1):
            if not isinstance(item, dict) or not item.get("item"):
                continue
            branches.append(
                {
                    "id": f"deferred-{index}",
                    "title": item["item"],
                    "kind": "secondary",
                    "priority": "DEFERRED",
                    "status": "PENDING",
                    "depends_on": [],
                    "evidence": [],
                }
            )

    task = {
        "task_id": f"migrated-{digest[:12]}",
        "title": mission["objective"],
        "description": "Migrated from VEGA Tree state schema 1.1.",
        "explicit_class": legacy["task_class"],
        "signals": {
            "estimated_files": max(len(branches), 1),
            "migration": True,
            "project_scale": legacy["task_class"] in {"T3", "T4"},
            "external_effect": False,
            "destructive": legacy["task_class"] == "T4",
            "cross_system": False,
            "irreversible": False,
        },
        "branches": [
            {
                "id": branch["id"],
                "title": branch["title"],
                "kind": branch["kind"],
                "priority": branch["priority"],
                "depends_on": branch["depends_on"],
            }
            for branch in branches
        ],
    }
    state = {
        "schema_version": "2.0",
        "engine_version": __version__,
        "workflow_ref": TREE_WORKFLOW_REF,
        "task": task,
        "task_class": compute_task_class(task)[0],
        "route": "tree",
        "phase": "branch_execution",
        "branches": branches,
        "evidence": [
            _evidence(
                "migration-source",
                "migration",
                mission["objective"],
                f"sha256:{digest}",
                timestamp,
                "PASS",
            ),
            *[
                _evidence(
                    f"legacy-global-{index}",
                    "legacy-observation",
                    str(item),
                    None,
                    timestamp,
                    "REVIEW_REQUIRED",
                )
                for index, item in enumerate(legacy.get("evidence", []), start=1)
            ],
        ],
        "history": _history_to_branch_execution(timestamp),
    }
    report = validate_state(state)
    if not report.valid:
        return GuardResult(
            "FAIL",
            "MIGRATION_OUTPUT_INVALID",
            "Migrated state did not pass VGTREE 2.0 validation.",
            {"validation": report.as_dict()},
        )
    return GuardResult(
        "PASS",
        "MIGRATION_READY",
        "Legacy state migrated in memory. Source data was not modified.",
        {
            "state": state,
            "source_digest": f"sha256:{digest}",
            "notes": [
                "Legacy caller-provided gate booleans were not promoted as proof.",
                "Legacy free-text evidence was retained as typed observations.",
                "Legacy verified or integrated branches require fresh re-verification.",
            ],
        },
    )


def migrate_state_file(input_path: str | Path, output_path: str | Path) -> GuardResult:
    source = Path(input_path)
    destination = Path(output_path)
    try:
        if source.resolve() == destination.resolve():
            return GuardResult(
                "FAIL",
                "MIGRATION_OVERWRITE_FORBIDDEN",
                "Migration output must differ from the source path.",
            )
    except OSError as exc:
        return GuardResult("FAIL", "MIGRATION_PATH_INVALID", str(exc))
    if destination.exists():
        return GuardResult(
            "BLOCKED",
            "MIGRATION_OUTPUT_EXISTS",
            "Migration never overwrites an existing output file.",
        )
    try:
        legacy = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return GuardResult("FAIL", "MIGRATION_SOURCE_NOT_FOUND", str(source))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return GuardResult("FAIL", "MIGRATION_SOURCE_INVALID", str(exc))

    migrated = migrate_state(legacy)
    if migrated.status != "PASS":
        return migrated
    saved = StateStore().save(
        destination, migrated.data["state"], create_only=True
    )
    if saved.code == "STATE_OUTPUT_EXISTS":
        return GuardResult(
            "BLOCKED",
            "MIGRATION_OUTPUT_EXISTS",
            "Migration never overwrites an existing output file.",
        )
    if saved.status != "PASS":
        return saved
    return GuardResult(
        "PASS",
        "MIGRATION_SAVED",
        "Migrated state was written without modifying the source.",
        {**migrated.data, "output": str(destination)},
    )


def _migrate_branch(
    branch: Any, kind: str, timestamp: str
) -> dict[str, Any] | None:
    if not isinstance(branch, dict) or not branch.get("id") or not branch.get("label"):
        return None
    old_status = branch.get("status", "missing")
    status = STATUS_MAP.get(old_status, "PENDING")
    accepted = branch.get("accepted_limitation") is True
    if accepted:
        status = "ACCEPTED_LIMITATION"
    priority = PRIORITY_MAP.get(branch.get("priority"), "P2")
    if kind == "primary" and priority == "DEFERRED":
        priority = "P2"

    evidence = [
        _evidence(
            f"{branch['id']}-legacy-{index}",
            "legacy-observation",
            str(item),
            None,
            timestamp,
            "REVIEW_REQUIRED",
        )
        for index, item in enumerate(branch.get("evidence", []), start=1)
    ]
    if status in {"BLOCKED", "ACCEPTED_LIMITATION"} and not evidence:
        evidence.append(
            _evidence(
                f"{branch['id']}-migration-record",
                "migration-record",
                branch["label"],
                None,
                timestamp,
                "REVIEW_REQUIRED",
            )
        )

    converted: dict[str, Any] = {
        "id": branch["id"],
        "title": branch["label"],
        "kind": kind,
        "priority": priority,
        "status": status,
        "depends_on": branch.get("dependencies", []),
        "evidence": evidence,
    }
    if status == "BLOCKED":
        converted["blocked_reason"] = branch.get("blocker") or "Legacy branch was blocked."
    if status == "ACCEPTED_LIMITATION":
        converted["limitation"] = {
            "scope": branch["label"],
            "consequence": branch.get("blocker") or "See the legacy state and evidence.",
            "owner": "legacy-unspecified",
            "accepted_at": timestamp,
        }
    return converted


def _evidence(
    evidence_id: str,
    evidence_type: str,
    subject: str,
    digest: str | None,
    timestamp: str,
    outcome: str,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": evidence_id,
        "type": evidence_type,
        "subject": subject,
        "method": "VGTREE schema 1.1 migration",
        "timestamp": timestamp,
        "outcome": outcome,
    }
    if digest:
        item["digest"] = digest
    elif outcome == "PASS":
        item["reference"] = f"legacy://{evidence_id}"
    return item


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _history_to_branch_execution(timestamp: str) -> list[dict[str, Any]]:
    phases = (
        "mission_understanding",
        "outcome_definition",
        "breadth_mapping",
        "branch_execution",
    )
    return [
        {
            "from": None if index == 0 else phases[index - 1],
            "to": phase,
            "timestamp": timestamp,
            "reason": "state migrated from schema 1.1",
        }
        for index, phase in enumerate(phases)
    ]
