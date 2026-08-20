"""VGTREE command-line entry point with stable JSON results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from vgtree.engine import VGTREEEngine
from vgtree.migration import migrate_state_file
from vgtree.models import GuardResult
from vgtree.obsidian import ObsidianWorkspace
from vgtree.store import StateStore
from vgtree.validation import validate_task


EXIT_CODES = {"PASS": 0, "FAIL": 1, "REVIEW_REQUIRED": 2, "BLOCKED": 3}


class CLIUsageError(Exception):
    pass


class JSONArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CLIUsageError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = JSONArgumentParser(
        prog="vgtree",
        description=(
            "VGTREE - local-first, no-telemetry tree workflows for AI agents "
            "and Obsidian."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify = subparsers.add_parser("classify", help="Classify and route a task.")
    classify.add_argument("--task", required=True, type=Path)
    classify.add_argument("--registry", type=Path)

    initialize = subparsers.add_parser("init", help="Create a new workflow state.")
    initialize.add_argument("--task", required=True, type=Path)
    initialize.add_argument("--state", required=True, type=Path)
    initialize.add_argument("--registry", type=Path)

    next_command = subparsers.add_parser("next", help="Evaluate and advance one phase.")
    next_command.add_argument("--state", required=True, type=Path)

    guard = subparsers.add_parser("guard", help="Evaluate a branch activity.")
    guard.add_argument("--state", required=True, type=Path)
    guard.add_argument("--branch", required=True)
    guard.add_argument("--activity", required=True)

    validate = subparsers.add_parser("validate", help="Validate a workflow state.")
    validate.add_argument("--state", required=True, type=Path)

    complete = subparsers.add_parser("complete", help="Evaluate final completion gates.")
    complete.add_argument("--state", required=True, type=Path)

    record = subparsers.add_parser(
        "record-evidence", help="Attach a typed evidence record."
    )
    record.add_argument("--state", required=True, type=Path)
    record.add_argument("--evidence", required=True, type=Path)
    record.add_argument("--branch")

    set_branch = subparsers.add_parser(
        "set-branch", help="Apply a legal evidence-gated branch transition."
    )
    set_branch.add_argument("--state", required=True, type=Path)
    set_branch.add_argument("--branch", required=True)
    set_branch.add_argument(
        "--status",
        required=True,
        choices=("PENDING", "IN_PROGRESS", "VERIFIED", "BLOCKED", "ACCEPTED_LIMITATION"),
    )
    set_branch.add_argument("--blocked-reason")
    set_branch.add_argument("--limitation", type=Path)

    migrate = subparsers.add_parser(
        "migrate-state", help="Migrate schema 1.1 state to a new 2.0 file."
    )
    migrate.add_argument("--input", required=True, type=Path)
    migrate.add_argument("--output", required=True, type=Path)

    obsidian = subparsers.add_parser("obsidian", help="Obsidian workspace tools.")
    obsidian_commands = obsidian.add_subparsers(
        dest="obsidian_command", required=True
    )
    audit = obsidian_commands.add_parser("audit", help="Audit an existing vault.")
    audit.add_argument("--vault", required=True, type=Path)
    audit.add_argument("--mode", required=True, choices=("core", "governed"))
    audit.add_argument("--live", action="store_true")
    plan = obsidian_commands.add_parser("plan", help="Generate a read-only change plan.")
    plan.add_argument("--vault", required=True, type=Path)
    plan.add_argument("--mode", required=True, choices=("core", "governed"))
    plan.add_argument("--output", required=True, type=Path)
    scaffold = obsidian_commands.add_parser(
        "scaffold", help="Create a new starter workspace."
    )
    scaffold.add_argument("--destination", required=True, type=Path)
    scaffold.add_argument("--mode", required=True, choices=("core", "governed"))
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = build_parser().parse_args(argv)
        result = _dispatch(arguments)
    except CLIUsageError as exc:
        result = GuardResult("FAIL", "CLI_USAGE_ERROR", str(exc))
    except Exception as exc:  # pragma: no cover - final safety envelope
        result = GuardResult(
            "FAIL",
            "CLI_INTERNAL_ERROR",
            f"Controlled internal error: {type(exc).__name__}: {exc}",
        )
    _emit(result)
    return EXIT_CODES.get(result.status, 1)


def _dispatch(arguments: argparse.Namespace) -> GuardResult:
    commands: dict[str, Callable[[argparse.Namespace], GuardResult]] = {
        "classify": _classify,
        "init": _initialize,
        "next": _next,
        "guard": _guard,
        "validate": _validate,
        "complete": _complete,
        "record-evidence": _record_evidence,
        "set-branch": _set_branch,
        "migrate-state": _migrate,
        "obsidian": _obsidian,
    }
    return commands[arguments.command](arguments)


def _classify(arguments: argparse.Namespace) -> GuardResult:
    loaded = _load_json(arguments.task, "TASK")
    if isinstance(loaded, GuardResult):
        return loaded
    engine = _engine_from_registry(arguments.registry)
    if isinstance(engine, GuardResult):
        return engine
    report = validate_task(loaded)
    if not report.valid:
        return GuardResult(
            "FAIL",
            "TASK_INVALID",
            "Task specification failed validation.",
            {"validation": report.as_dict()},
        )
    decision = engine.classify(loaded)
    return GuardResult(
        "PASS",
        "CLASSIFIED",
        "Task classification and route were computed.",
        {"decision": decision.as_dict()},
    )


def _initialize(arguments: argparse.Namespace) -> GuardResult:
    if arguments.state.exists():
        return GuardResult(
            "BLOCKED",
            "STATE_OUTPUT_EXISTS",
            "Initialization never overwrites an existing state file.",
        )
    loaded = _load_json(arguments.task, "TASK")
    if isinstance(loaded, GuardResult):
        return loaded
    engine = _engine_from_registry(arguments.registry)
    if isinstance(engine, GuardResult):
        return engine
    result = engine.initialize(loaded)
    if result.status != "PASS":
        return result
    saved = StateStore().save(
        arguments.state, result.data["state"], create_only=True
    )
    if saved.status != "PASS":
        return saved
    return GuardResult(
        "PASS",
        "INITIALIZED",
        "Workflow state initialized and saved.",
        result.data,
    )


def _next(arguments: argparse.Namespace) -> GuardResult:
    return _mutate_state(arguments.state, VGTREEEngine().next)


def _guard(arguments: argparse.Namespace) -> GuardResult:
    loaded = StateStore().load(arguments.state)
    if loaded.status != "PASS":
        return loaded
    return VGTREEEngine().guard(
        loaded.data["state"], arguments.branch, arguments.activity
    )


def _validate(arguments: argparse.Namespace) -> GuardResult:
    loaded = StateStore().load(arguments.state)
    if loaded.status != "PASS":
        return loaded
    report = VGTREEEngine().validate(loaded.data["state"])
    return GuardResult(
        "PASS" if report.valid else "FAIL",
        "STATE_VALID" if report.valid else "STATE_INVALID",
        "Workflow state passed validation." if report.valid else "Validation failed.",
        {"validation": report.as_dict()},
    )


def _complete(arguments: argparse.Namespace) -> GuardResult:
    return _mutate_state(arguments.state, VGTREEEngine().complete)


def _record_evidence(arguments: argparse.Namespace) -> GuardResult:
    evidence = _load_json(arguments.evidence, "EVIDENCE")
    if isinstance(evidence, GuardResult):
        return evidence
    return _mutate_state(
        arguments.state,
        lambda state: VGTREEEngine().record_evidence(
            state, evidence, branch_id=arguments.branch
        ),
    )


def _set_branch(arguments: argparse.Namespace) -> GuardResult:
    limitation = None
    if arguments.limitation is not None:
        limitation = _load_json(arguments.limitation, "LIMITATION")
        if isinstance(limitation, GuardResult):
            return limitation
    return _mutate_state(
        arguments.state,
        lambda state: VGTREEEngine().set_branch(
            state,
            arguments.branch,
            arguments.status,
            blocked_reason=arguments.blocked_reason,
            limitation=limitation,
        ),
    )


def _migrate(arguments: argparse.Namespace) -> GuardResult:
    return migrate_state_file(arguments.input, arguments.output)


def _obsidian(arguments: argparse.Namespace) -> GuardResult:
    workspace = ObsidianWorkspace()
    if arguments.obsidian_command == "audit":
        return workspace.audit(arguments.vault, arguments.mode, live=arguments.live)
    if arguments.obsidian_command == "scaffold":
        return workspace.scaffold(arguments.destination, arguments.mode)
    if arguments.obsidian_command == "plan":
        return _obsidian_plan(workspace, arguments.vault, arguments.mode, arguments.output)
    return GuardResult("FAIL", "CLI_USAGE_ERROR", "Unknown Obsidian command.")


def _obsidian_plan(
    workspace: ObsidianWorkspace, vault: Path, mode: str, output: Path
) -> GuardResult:
    try:
        vault_resolved = vault.resolve()
        output_resolved = output.resolve()
    except OSError as exc:
        return GuardResult("FAIL", "OBSIDIAN_PLAN_PATH_INVALID", str(exc))
    if output_resolved == vault_resolved or vault_resolved in output_resolved.parents:
        return GuardResult(
            "BLOCKED",
            "OBSIDIAN_PLAN_OUTPUT_UNSAFE",
            "A read-only plan output must be outside the audited vault.",
        )
    if output.exists():
        return GuardResult(
            "BLOCKED",
            "OBSIDIAN_PLAN_OUTPUT_EXISTS",
            "Plan generation never overwrites an existing output file.",
        )
    result = workspace.plan(vault, mode)
    if result.status != "PASS":
        return result
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result.as_dict(), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        return GuardResult(
            "BLOCKED", "OBSIDIAN_PLAN_OUTPUT_EXISTS", "Plan output already exists."
        )
    except (OSError, TypeError, ValueError) as exc:
        return GuardResult("FAIL", "OBSIDIAN_PLAN_WRITE_FAILED", str(exc))
    return GuardResult(
        "PASS",
        "OBSIDIAN_PLAN_SAVED",
        "Read-only workspace plan was written outside the vault.",
        {**result.data, "output": str(output)},
    )


def _mutate_state(
    state_path: Path, operation: Callable[[dict[str, Any]], GuardResult]
) -> GuardResult:
    return StateStore().update(state_path, operation)


def _load_json(path: Path, prefix: str) -> Any | GuardResult:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return GuardResult("FAIL", f"{prefix}_NOT_FOUND", f"File not found: {path}")
    except (OSError, UnicodeError) as exc:
        return GuardResult("FAIL", f"{prefix}_READ_FAILED", str(exc))
    except json.JSONDecodeError as exc:
        return GuardResult(
            "FAIL",
            f"{prefix}_JSON_INVALID",
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}.",
        )


def _engine_from_registry(path: Path | None) -> VGTREEEngine | GuardResult:
    if path is None:
        return VGTREEEngine()
    loaded = _load_json(path, "WORKFLOW_REGISTRY")
    if isinstance(loaded, GuardResult):
        return loaded
    if not isinstance(loaded, dict) or set(loaded) != {"workflows"}:
        return GuardResult(
            "FAIL",
            "WORKFLOW_REGISTRY_INVALID",
            "Registry must contain only a workflows array.",
        )
    workflows = loaded.get("workflows")
    if not isinstance(workflows, list):
        return GuardResult(
            "FAIL", "WORKFLOW_REGISTRY_INVALID", "workflows must be an array."
        )
    registered: set[str] = set()
    for item in workflows:
        if (
            not isinstance(item, dict)
            or set(item) != {"workflow_ref", "status"}
            or not isinstance(item.get("workflow_ref"), str)
            or item.get("status") not in {"ACTIVE", "VERIFIED", "INACTIVE"}
        ):
            return GuardResult(
                "FAIL",
                "WORKFLOW_REGISTRY_INVALID",
                "Each workflow requires workflow_ref and a valid status.",
            )
        if item["status"] in {"ACTIVE", "VERIFIED"}:
            registered.add(item["workflow_ref"])
    return VGTREEEngine(registered_workflows=registered)


def _emit(result: GuardResult) -> None:
    json.dump(result.as_dict(), sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
