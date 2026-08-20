# VGTREE 1.1 OpenAI submission package

This document is the human-readable source for the VGTREE 1.1 Skills-only submission. The machine-checkable listing and cases live in:

- `submission/openai-listing-v1.1.0.json`
- `submission/openai-test-cases-v1.1.0.json`

Run `python scripts/validate_submission.py` before copying anything into the Portal.

## Official submission basis

OpenAI's current documentation explicitly permits a Skills-only plugin. It requires public listing and policy fields, a verified developer or business identity, a final skill bundle, starter prompts, at least five positive and three negative test cases, availability selection, release notes, policy attestations, and a final locally tested file tree.

- [Submit plugins](https://developers.openai.com/plugins/deploy/submission)
- [Build skills](https://developers.openai.com/plugins/build/skills)
- [Package your plugin](https://developers.openai.com/plugins/build/plugins)

The plugin has no MCP server, authentication, account, hosted service, Plugin UI, or telemetry. MCP, tool annotation, demo credential, domain challenge, and CSP fields are therefore not part of this submission.

## Portal Info fields

| Field | Exact value |
|---|---|
| Submission type | Skills only |
| Name | VGTREE |
| Category | Productivity |
| Short description | Branch complex work into verifiable outcomes. |
| Website | https://scandium1102.github.io/vgtree/ |
| Support | https://github.com/scandium1102/vgtree/issues |
| Privacy | https://scandium1102.github.io/vgtree/privacy/ |
| Terms | https://scandium1102.github.io/vgtree/terms/ |
| Developer Identity | The matching verified individual identity, selected only after the release owner completes verification personally |
| Availability | Every country or region the Portal allows |
| Screenshots | None; VGTREE 1.1 has no Plugin UI |

Long description:

> VGTREE maps complex work into evidence-backed branches before the agent goes deep. It helps ChatGPT and Codex plan, execute, and verify multi-step outcomes with coverage gates, inspectable receipts, honest fallbacks, and optional deterministic CLI enforcement. It also includes UID-first knowledge architecture and local-first Obsidian workspace workflows. No VGTREE account, hosted service, or telemetry is required.

## Exact upload

Upload `vgtree-plugin-1.1.0.zip` from the GitHub Release candidate. Before upload:

1. Find its line in `SHA256SUMS`.
2. Recompute the local SHA-256 digest and require an exact match.
3. Inspect the archive for `.codex-plugin/plugin.json`, six `skills/*/SKILL.md` files, shared schemas, templates, references, and declared assets.
4. Run the official Plugin validator and all six official Skill validators against the extracted archive.
5. Keep the verified archive unchanged from scan through submission.

Do not substitute `vgtree-skills-1.1.0.zip`; that archive is the GitHub convenience package without the full plugin identity.

## Starter prompts

1. **Capability Map** — Map this complex outcome into a VGTREE Capability Map with required branches, dependencies, shared interfaces, risk owners, minimum viable states, and final acceptance before implementation begins.
2. **Wide-pass execution** — Run a VGTREE wide pass for this multi-step project, record baseline coverage for every required branch, and show what still blocks safe deep execution.
3. **Receipt verification** — Review these VGTREE Tool Receipts and workflow state, distinguish baseline from completion evidence, and report which branch, integration, and final-verification gates are actually satisfied.
4. **Obsidian read-only audit** — Audit this Obsidian workspace in VGTREE Core mode without changing any notes, then report missing canonical surfaces and a reversible improvement plan.
5. **UID-first knowledge architecture** — Design a UID-first VGTREE knowledge architecture for this second-brain project, including canonical ownership, registries, provenance, lineage, readback, and rollback boundaries.

## Reviewer test suite

The eight exact cases and fixtures are in `submission/openai-test-cases-v1.1.0.json`.

Positive cases:

1. Build a complete Capability Map for a multi-surface release.
2. Run a wide pass and block premature depth.
3. Distinguish baseline evidence from a completion Receipt.
4. Audit an existing Obsidian workspace without mutation.
5. Design a greenfield governed UID-first architecture without inventing existing state.

Negative cases:

1. Do not perform GitHub, PyPI, or Portal publication without the applicable current authorization.
2. Do not reorganize, rewrite, or delete an existing Obsidian vault; offer read-only audit and planning.
3. Do not fabricate Engine `PASS` when the CLI is absent; use SKILL_ONLY, disclose `engine_validation=NOT_RUN`, and cap status at `REVIEW_REQUIRED`.

The cases require no VGTREE account, private workspace context, private network, MFA, SMS, email confirmation, or reviewer credentials.

## Release notes

> Initial public Skills-only submission of VGTREE 1.1. Includes six focused Skills, ENGINE and SKILL_ONLY runtime modes, Capability Maps, Coverage Gates, Tool Receipts, Context Budget controls, UID-first knowledge architecture, and local-first Obsidian workflows. No authentication, MCP server, Plugin UI, hosted data, or telemetry is included.

## Portal readiness and authorization gates

Portal login does not prove Apps Management write access or individual verification. Read those statuses live before draft creation.

1. The release owner personally completes Individual verification. The agent does not inspect, store, or upload identity documents.
2. Obtain explicit authorization before creating the Skills-only draft or uploading the archive.
3. Enter the exact validated fields, prompts, cases, availability, release notes, and attestations.
4. Run the Portal scan and read back every field and discovered Skill.
5. Obtain new action-time authorization immediately before `Submit for Review`.
6. After approval, obtain a separate authorization immediately before `Publish`.
7. After publication, verify installation and actual Skill triggering from both ChatGPT and Codex in the universal Plugins Directory.

Until those live steps happen, submission status remains `REVIEW_REQUIRED`; local package validation is not a claim of Portal acceptance or publication.
