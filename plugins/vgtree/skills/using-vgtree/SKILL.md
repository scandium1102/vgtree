---
name: using-vgtree
description: Use when a complex, multi-surface, migration, release, or high-risk task needs deterministic routing, persistent tree state, evidence gates, and an honest completion decision.
---

# Using VGTREE

Use VGTREE as the thin control plane. Keep domain work in the relevant tools and workflows.

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
2. Create a strict task JSON. Populate every signal from observed scope; an explicit class may upgrade risk but must never lower it.
3. Run:

```text
vgtree classify --task task.json
```

4. Follow the returned route. For `direct`, keep the task bounded. For `specialized`, use only a registry-verified full match. For `tree`, initialize persistent state:

```text
vgtree init --task task.json --state .vgtree/tasks/<task-id>.json
```

## Execute a Tree route

Advance early phases with `vgtree next --state <state>`. Before starting a branch, run `vgtree guard --state <state> --branch <id> --activity <activity>` using the command-safety contract above.

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

If the CLI is unavailable, report `BLOCKED` or install it only when installation is authorized. Do not simulate a successful VGTREE run in prose.
