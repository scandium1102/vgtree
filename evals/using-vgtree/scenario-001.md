# using-vgtree evaluation: complex release task

Date: 2026-08-20

## Scenario

Refactor authentication across 12 files, evaluate a database migration, update an Obsidian project map, and publish a GitHub release. Describe routing, execution order, evidence gates, and the completion condition.

## Baseline without the skill

The agent produced a strong conceptual T3 plan with primary branches and domain gates. It explicitly identified that it lacked machine-verifiable workflow steps, concrete state persistence, exact test commands, and remote readback evidence.

## Result with the skill

The agent used deterministic task JSON and an exact sequence of `classify`, `init`, `next`, `guard`, `set-branch`, `record-evidence`, `validate`, and `complete` commands. It correctly preserved database evaluation-only scope, dependency order, exit-code meanings, typed integration/final evidence, and GitHub remote readback as a separate external proof.

## Improvement

- Routing changed from a prose judgment to schema-validated deterministic classification.
- Branch state, dependency guards, evidence, phase history, and completion became machine-verifiable.
- The completion claim was tied to `status=PASS`, `code=COMPLETE`, state readback, and external readback.

## Remaining limitations

- Domain-specific security, database rollback, Vault governance, and remote release checks still require their own tools.
- Local source invocation was required during development because the release CLI was not yet clean-room installed.
- Evidence freshness and referenced-artifact digest verification need release hardening.
- Specialized registry input needs an explicit CLI surface.

Verdict: PASS with release-hardening follow-ups.
