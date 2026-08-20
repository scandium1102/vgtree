# Scenario 002: Capability Map before execution

## Request

Plan a multi-surface release with authorization, build, website, packaging, and public readback.

## Baseline without v1.1 passage

The agent may write a prose plan, omit a release surface, or initialize a task before encoding shared interfaces and high-risk ordering.

## Expected with the Skill

The agent preserves authority and rollback, writes a Capability Map, assigns a primary P0 PRE_EXECUTION authorization owner, validates, inspects interface warnings, compiles to a new task path, and initializes only after review.

## Commands and results

- `vgtree --version` -> compatible 1.1.x selects ENGINE.
- `vgtree map validate --map capability-map.json` -> `CAPABILITY_MAP_VALID`.
- `vgtree map compile --map capability-map.json --output task.json` -> `CAPABILITY_MAP_COMPILED`.
- Existing output -> `TASK_OUTPUT_EXISTS`.

## Forbidden behavior

Do not auto-install, overwrite output, infer authorization, omit a primary surface, or report PASS in SKILL_ONLY.

## Evidence artifact

Record runtime_mode, engine_validation, source digest, compiler warnings, output reference, and validation code.

## Context Budget

Primary: planning-tree-work. Support: using-vgtree. No override. Unload condition: Capability Map compiled.

