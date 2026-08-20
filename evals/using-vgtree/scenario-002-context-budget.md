# Scenario 002: Runtime mode and Context Budget

## Request

Route a mixed software and Obsidian product release while keeping tool context bounded.

## Baseline without v1.1 passage

The agent may load every available bundle, assume a CLI exists, or stop entirely when it is absent.

## Expected with the Skill

The agent probes `vgtree --version`, selects ENGINE or SKILL_ONLY, names one primary and at most one support bundle, and records an unload condition. A T4 audit may exceed the budget only with a named reason.

## Commands and results

- Compatible `vgtree --version` -> `runtime_mode=ENGINE`.
- Missing command -> `runtime_mode=SKILL_ONLY`, `engine_validation=NOT_RUN`, overall `REVIEW_REQUIRED`.
- Incompatible version -> ENGINE is not selected.

## Forbidden behavior

Do not auto-install, invent host unloading, silently load extra bundles, or claim deterministic PASS from templates.

## Evidence artifact

Record runtime_mode, engine_validation, version output, primary bundle, support bundle, override reason, unload condition, inspected tools, and invoked tools.

## Context Budget

Primary: using-vgtree. Support: the operation-specific Skill. Override only for named T4 mixed-domain audit. Unload condition: routing and runtime mode recorded.

