---
name: planning-tree-work
description: Use when planning a complex task as a breadth-first branch DAG with explicit priorities, dependencies, Definition of Done, evidence requirements, and deferred scope before execution begins.
---

# Planning Tree Work

Create an executable control-plane artifact, not only a prose roadmap.

## Runtime mode

Run `vgtree --version` without installing software. Use `ENGINE` only for a compatible 1.1.x CLI. Otherwise use `SKILL_ONLY` and the packaged resources under `../../shared/`. Do not install VGTREE automatically.

In `SKILL_ONLY`, report `runtime_mode=SKILL_ONLY`, `engine_validation=NOT_RUN`, and an overall status no higher than `REVIEW_REQUIRED`. The fallback may plan, record, and review work, but it cannot claim that deterministic VGTREE gates returned `PASS`. Read `../../shared/references/runtime-modes.md` when choosing or reporting the mode.

## Establish the mission

Record the primary outcome, explicit non-goals, authorization boundaries, affected systems, rollback context, and the evidence needed to prove the final outcome. Inspect the real workspace before estimating scope.

For tree-scale work, write `capability-map.json` before task state. Direct T0/T1 work stays lightweight. Do not select a lower class to avoid Tree execution.

## Map breadth before depth

List all outcome surfaces before designing implementation details. Separate:

- `primary`: required for the requested outcome;
- `secondary`: useful but not completion-critical;
- `DEFERRED`: explicitly out of the current critical path;
- cross-cutting safety, integration, privacy, release, and worktree concerns, represented as real branches when they have completion consequences.

Every branch needs:

```json
{
  "id": "stable-lowercase-id",
  "title": "Outcome-oriented label",
  "kind": "primary",
  "priority": "P0",
  "coverage_required": true,
  "depends_on": [],
  "minimum_viable_state": ["Observable wide-pass baseline"],
  "baseline_evidence_requirements": ["Fresh baseline inspection"],
  "definition_of_done": ["Observable outcome"],
  "acceptance_evidence": ["Fresh command or readback evidence"],
  "shared_interfaces": ["named-interface"],
  "deferred_details": [],
  "stop_condition": "Stop when the decision is ready or the branch is blocked"
}
```

Use `depends_on` only for real prerequisites. Reject missing nodes, self-dependencies, and cycles. A primary branch must not be `DEFERRED`.

## Make the critical path honest

1. Place permission, compatibility, migration assessment, and destructive-risk decisions before dependent implementation.
2. Put integration after the branches it combines.
3. Put external publication after tests, artifact integrity, security, and authorization gates.
4. Keep cleanup and optional optimizations deferred until the primary outcome is verified.
5. Give each branch a stop condition so investigation cannot expand without a decision delta.

## Validate the plan

Preserve repository instructions, authorization, rollback, and protected paths. Encode every high-risk gate as a `PRE_EXECUTION` owner branch plus real dependency edges. Then, in `ENGINE`:

```text
vgtree map validate --map capability-map.json
vgtree map compile --map capability-map.json --output task.json
vgtree classify --task task.json
vgtree init --task task.json --state state.json
vgtree validate --state state.json
```

Inspect compiler warnings for unconsumed interfaces. Initialize only after validation and owner review when required.

In `SKILL_ONLY`, copy `../../shared/templates/capability-map.json`, check it against `../../shared/schemas/capability-map.schema.json`, and record the review in `skill-only-work-record.json`. Do not install a CLI, compile a task, or claim validation `PASS`; report `engine_validation=NOT_RUN` and overall `REVIEW_REQUIRED`.

Before execution, be able to answer:

- Which branches are required for overall completion?
- Which exact evidence satisfies each Definition of Done?
- Which branch owns every external effect and permission gate?
- What remains safe to report if a primary branch is blocked?
- What is intentionally deferred, and why?

Never infer unknown repositories, identities, environments, versions, approvals, or remote targets merely to make the plan look complete.
