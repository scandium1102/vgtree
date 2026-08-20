# VGTREE Current Workflow Assessment

Date: 2026-08-20
Status: Approved implementation baseline
Scope: `WF-VEGA-TREE@1.0`, its policy helper, state schema, tests, and V2 Vault integration

## Executive verdict

The current VEGA Tree Workflow is a strong governance prototype, but it is not yet a complete distributable product. Its strongest qualities are the thin control-plane model, breadth-before-depth execution, branch and rabbit-hole guards, explicit evidence vocabulary, and deterministic routing tests. Its main weakness is that several safety-critical decisions still trust caller-provided values instead of deriving and validating them.

VGTREE v1.0 should preserve the existing workflow reference for compatibility while introducing a real execution engine, a stricter state schema, an installable CLI and Python API, composable Agent Skills, and an Obsidian starter kit.

## What is already valuable

1. T0-T4 complexity routing keeps simple tasks lightweight and sends complex tasks to Tree execution.
2. Primary, secondary, deferred, and blocked branches make breadth and priority visible.
3. Rabbit-hole, branch-completion, integration, and final-completion concepts provide a useful control plane.
4. Evidence states distinguish verified outcomes from assertions.
5. The current helper has deterministic unit tests and produces inspectable JSON.
6. The workflow is already linked into the V2 Vault's project and governance model.

## Confirmed defects and unsafe edge cases

The following cases were reproduced against the current implementation:

| Area | Reproduced behavior | Required correction |
|---|---|---|
| Classification | A task marked `T0` can remain direct even when migration and project-scale signals are true. | Derive a minimum task class from validated signals. Explicit input may upgrade, never downgrade. |
| Specialized workflow routing | An arbitrary unregistered workflow reference is accepted when the caller sets `specialized_full_match=true`. | Require structured match evidence and verify the workflow against a registry. |
| Input validation | A non-integer `estimated_files` value raises an uncaught exception. | Return a stable validation result and exit code. |
| Dependency integrity | Missing branch references and invalid primary `DEFERRED` priority are accepted. | Validate the dependency DAG, priorities, missing nodes, self-edges, and cycles. |
| Completion evidence | A blocked branch with `accepted_limitation=true` can pass without supporting evidence. | Require typed evidence and an explicit accepted-limitation record. |
| Phase integrity | The stop condition can pass during `mission_understanding`. | Enforce legal state transitions and phase-specific gates. |
| Empty data | Proxy metric calculation crashes on an empty list. | Return a defined empty result or validation failure. |
| Schema strictness | Nested unknown fields and semantic inconsistencies pass JSON Schema validation. | Use strict nested schemas plus semantic validation. |

## Productization gaps

- No execution state machine or legal transition model.
- No atomic persistence or task lock.
- No stable public Python package or command-line interface.
- No schema migration from the current internal state format.
- No computed completion gates; caller-provided booleans are trusted.
- No registry-backed specialized workflow match.
- No distributable OpenAI plugin or Agent Skills.
- No Obsidian audit, plan, scaffold, or starter vault.
- No CI, release automation, security policy, privacy policy, or support surface.
- Current documents contain deployment-specific V2 concepts that must not leak into the public generic core.

## Product boundaries

### Public VGTREE core

- Generic classification, tree planning, execution state, guards, verification, and completion.
- Core and Governed UID architecture modes.
- Obsidian audit, plan, and empty-destination scaffold commands.
- Six composable Agent Skills.
- Skills-only OpenAI plugin.
- Local-first operation with no telemetry and no network requirement.

### Private deployment adapter

- Deployment-specific project registry fields and UID namespaces.
- V2 Vault rules, canonical paths, private project references, and owner data.
- Any future connector to private workflows or runtime services.

The private adapter is not part of the public repository.

## Release recommendation

Proceed with productization only after the following are all true:

1. Every reproduced defect has a failing regression test followed by a passing implementation.
2. The engine, CLI, schemas, plugin, six skills, and Obsidian kit pass automated verification.
3. Public files pass secret, private-path, personal-data, and packaging scans.
4. A clean-room install from the release artifact succeeds.
5. GitHub release assets and public policy URLs exist.
6. OpenAI Plugin Directory submission prerequisites are verified at submission time.
