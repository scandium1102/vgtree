# Changelog

All notable changes to VGTREE are documented here.

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
