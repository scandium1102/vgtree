---
name: planning-tree-work
description: Use when planning a complex task as a breadth-first branch DAG with explicit priorities, dependencies, Definition of Done, evidence requirements, and deferred scope before execution begins.
---

# Planning Tree Work

Create an executable control-plane artifact, not only a prose roadmap.

## Establish the mission

Record the primary outcome, explicit non-goals, authorization boundaries, affected systems, rollback context, and the evidence needed to prove the final outcome. Inspect the real workspace before estimating scope.

Create task signals and run `vgtree classify --task <task.json>`. Do not select a lower class to avoid Tree execution.

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
  "depends_on": [],
  "definition_of_done": ["Observable outcome"],
  "evidence_requirements": ["Fresh command or readback evidence"],
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

Initialize it with `vgtree init --task <task.json> --state <state.json>`, then run `vgtree validate --state <state.json>`. Treat validation failure as a planning defect.

Before execution, be able to answer:

- Which branches are required for overall completion?
- Which exact evidence satisfies each Definition of Done?
- Which branch owns every external effect and permission gate?
- What remains safe to report if a primary branch is blocked?
- What is intentionally deferred, and why?

Never infer unknown repositories, identities, environments, versions, approvals, or remote targets merely to make the plan look complete.
