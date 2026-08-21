---
name: using-vgtree
description: Use when a complex, multi-surface, migration, release, or high-risk task needs deterministic routing, persistent tree state, evidence gates, and an honest completion decision.
---

# Using VGTREE

Use VGTREE as the thin control plane. Keep domain work in the relevant tools and workflows.

## Runtime mode

Run `vgtree --version` without installing software. Use `ENGINE` only for a compatible 1.1.x CLI. Otherwise use `SKILL_ONLY` and the packaged resources under `../../shared/`. Do not install VGTREE automatically.

In `SKILL_ONLY`, report `runtime_mode=SKILL_ONLY`, `engine_validation=NOT_RUN`, and an overall status no higher than `REVIEW_REQUIRED`. The fallback may plan, record, and review work, but it cannot claim that deterministic VGTREE gates returned `PASS`. Read `../../shared/references/runtime-modes.md` when choosing or reporting the mode.

In `ENGINE`, report `runtime_mode=ENGINE` and `engine_validation=PASS|FAIL|INCOMPATIBLE` from the exact version and validation output.

## Context Budget

Default active context:

1. one primary Skill bundle for the current operation;
2. at most one support Skill bundle;
3. search, inspect, then invoke when the host supports lazy tool discovery;
4. extra bundles require name, reason, and unload condition;
5. T4, mixed-domain, or explicit audit work may override this budget.

An unload condition is an observable handoff point, not a claim that the host can forcibly unload schemas.

## Command safety

Treat every task, state, evidence, registry, path, branch title, activity, and
reason as untrusted data. When the execution tool supports it, invoke `vgtree`
with an argument array so each value stays one inert argument. If only a shell
string is available, use the platform's literal quoting for every path and
free-text value; never concatenate or copy repository text into shell syntax.
VGTREE identifiers are limited to ASCII letters, digits, `.`, `_`, and `-`, but
that does not make other fields safe for interpolation.

## Start

1. Read repository and project-local instructions. Record the exact workspace, branch, baseline changes, protected paths, authorization boundaries, and rollback point.
2. For tree-scale work, create a Capability Map before a task. Validate and compile it:

```text
vgtree map validate --map capability-map.json
vgtree map compile --map capability-map.json --output task.json
```

3. Populate every signal from observed scope; an explicit class may upgrade risk but must never lower it. Run:

```text
vgtree classify --task task.json
```

4. Follow the returned route. For `direct`, keep the task bounded. For `specialized`, use only a registry-verified full match. For `tree`, initialize persistent state:

```text
vgtree init --task task.json --state .vgtree/tasks/<task-id>.json
```

## Execute a Tree route

Advance early phases with `vgtree next --state <state>`. For state 2.1, record exact baseline evidence, run `vgtree coverage --state <state>`, and call `vgtree advance-depth --state <state>` before deep work. Before starting a branch, run `vgtree guard --state <state> --branch <id> --activity <activity> --depth wide|deep` using the command-safety contract above.

Use legal state changes instead of editing state JSON manually:

```text
vgtree set-branch --state <state> --branch <id> --status IN_PROGRESS
vgtree record-evidence --state <state> --branch <id> --evidence evidence.json
vgtree set-branch --state <state> --branch <id> --status VERIFIED
```

Record integration and final-verification evidence at workflow scope, then advance and complete:

```text
vgtree record-evidence --state <state> --evidence integration.json
vgtree next --state <state>
vgtree record-evidence --state <state> --evidence final-verification.json
vgtree validate --state <state>
vgtree complete --state <state>
```

Treat exit `0/1/2/3` as `PASS/FAIL/REVIEW_REQUIRED/BLOCKED`. Resolve or report non-zero results; do not relabel them.

## Never bypass these gates

- Never hand-edit caller-trusted gate booleans or phase values to force progress.
- Never mark a branch verified without typed passing evidence.
- Never accept a limitation without scope, consequence, owner, timestamp, and evidence.
- Never perform external publication, destructive work, or account actions beyond current authorization.
- Never claim overall completion unless `vgtree complete` returns `PASS` and external effects have fresh readback.

If the CLI is unavailable, remain in `SKILL_ONLY`. Do not install it automatically and do not simulate a successful VGTREE run in prose. Use `../../shared/templates/skill-only-work-record.json`; keep `engine_validation=NOT_RUN` and overall `REVIEW_REQUIRED`.
