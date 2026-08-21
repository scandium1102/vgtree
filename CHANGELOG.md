# Changelog

All notable changes to VGTREE are documented here.

## [1.1.0] - 2026-08-21

### Added

- Capability Map 1.0 validation, deterministic task compilation, exact source digests, and map CLI commands.
- State 2.1 opt-in Coverage Gate with computed wide-pass evidence, one-way deep transitions, and depth-aware guards while preserving state 2.0.
- Tool Receipt 1.0 validation, explicit-root containment, exact-byte evidence binding, and create-only receipt CLI output.
- ENGINE and SKILL_ONLY modes across all six Skills, shared offline schemas/templates, Context Budget guidance, and deterministic evaluation fixtures.
- `vgtree --version`, English and Traditional Chinese product documentation, GitHub Pages surfaces, release bundles, and PyPI Trusted Publishing preparation.

### Trust boundaries

- SKILL_ONLY never installs the Engine, reports `engine_validation=NOT_RUN`, and cannot claim overall `PASS`.
- Receipt validation proves structure and byte binding, not the truth of an external tool's claims.
- No account, hosted VGTREE service, MCP server, telemetry, analytics, or automatic existing-vault mutation was added.

## [1.0.0] - 2026-08-20

### Added

- Deterministic T0-T4 classification and registry-verified specialized routing.
- Strict task/state schemas, branch DAG validation, and state migration from VEGA Tree 1.1.
- Evidence-gated engine, legal branch transitions, atomic state storage, and JSON CLI.
- Read-only Obsidian audit/plan and safe Core/Governed starter scaffold.
- Six evaluated Agent Skills and a skills-only OpenAI plugin.
- English and Traditional Chinese documentation, public policies, examples, and release verification.

### Security

- Restricted command-adjacent identifiers and documented argument-array handling for untrusted input.
- Recomputed task class, phase/history coherence, and evidence gates during state validation.
- Bound every mutable state branch to the immutable branch specification embedded in its task.
- Bounded DAG size and replaced recursive cycle traversal with an iterative algorithm.
- Serialized state read-modify-write transactions and made first-write commits non-overwriting.
- Contained Obsidian audit reads to regular files inside the selected vault with size limits.
- Split release build and publish privileges, pinned GitHub Actions, and hash-locked build dependencies.
