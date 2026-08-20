# planning-tree-work evaluation: cross-repository release plan

Date: 2026-08-20

## Baseline

The agent produced a thoughtful cross-repository DAG and release gates, but invented abstract repository names and acknowledged that no machine-valid task artifact, locked baseline, or CI-checkable plan existed.

## With the skill

The agent produced schema-valid task JSON, received a deterministic `T3/tree` route, initialized state schema 2.0, and passed VGTREE validation. It replaced assumed repository identities with an inventory branch, represented workspace isolation, migration disposition, security/privacy, external authorization, and post-release readback as real dependencies, and kept cleanup as secondary deferred work.

## Improvement and refinement

- Every branch gained observable Definition of Done and evidence requirements.
- Missing-node, self-dependency, cycle, and primary/deferred conflicts became machine-checkable.
- The evaluation exposed that stop conditions were only prose. VGTREE therefore added a dedicated optional `stop_condition` branch field to the task and state schemas.

Verdict: PASS after schema refinement.
