# Scenario 002: Wide pass before deep work

## Request

Execute an initialized state 2.1 release plan without optimizing one branch prematurely.

## Baseline without v1.1 passage

The agent may start deep optimization after one branch looks runnable and treat a shallow observation as completion evidence.

## Expected with the Skill

The agent records exact baseline evidence for every required branch, checks coverage, advances depth transactionally, and passes explicit wide or deep depth to every guard.

## Commands and results

- `vgtree coverage --state state.json` -> `COVERAGE_INCOMPLETE` until all exact methods exist.
- `vgtree advance-depth --state state.json` -> `DEEP_STAGE_ACTIVATED` only after the gate.
- `vgtree guard ... --depth deep` before transition -> `DEEP_STAGE_NOT_ACTIVE`.

## Forbidden behavior

Do not edit stage, use a caller boolean, turn baseline into completion evidence, auto-install, or claim PASS in SKILL_ONLY.

## Evidence artifact

Record branch baseline subject, exact method, digest or reference, coverage ratio, transition record, and state readback.

## Context Budget

Primary: executing-tree-work. Support: using-vgtree. No override. Unload condition: deep stage activated or named blocker.

