---
name: governing-knowledge-architecture
description: Use when designing or auditing a reusable knowledge architecture with stable identity, ownership, registries, discoverability, provenance, hashes, transactions, and rollback across projects or an Obsidian workspace.
---

# Governing Knowledge Architecture

Build one authority model with two governance strengths. Core and Governed modes must not become competing versions of current truth.

## Runtime mode

Run `vgtree --version` without installing software. Use `ENGINE` only for a compatible 1.1.x CLI. Otherwise use `SKILL_ONLY` and the packaged resources under `../../shared/`. Do not install VGTREE automatically.

In `SKILL_ONLY`, report `runtime_mode=SKILL_ONLY`, `engine_validation=NOT_RUN`, and an overall status no higher than `REVIEW_REQUIRED`. The fallback may plan, record, and review work, but it cannot claim that deterministic VGTREE gates returned `PASS`. Read `../../shared/references/runtime-modes.md` when choosing or reporting the mode.

In `SKILL_ONLY`, the architecture guidance remains usable for planning and read-only review. Do not install VGTREE or turn guidance into an unapproved mutation. Use the packaged work record and preserve unknown ownership, UID, lineage, or path as `REVIEW_REQUIRED`.

## Choose the mode

### Core mode

Use for ordinary personal and project knowledge. Require:

- one stable project UID per project;
- one canonical owner and root;
- a project registry;
- discoverable Home, Map, Status, and Todo surfaces;
- links to the actual outcome and evidence;
- rollback for destructive or multi-file work.

### Governed mode

Use when migration, formal publication, research evidence, finance, applications, or high-value records require fail-closed handling. Keep Core identity and add:

- a file UID for every managed file;
- a raw-byte SHA-256 content hash;
- provenance and parent/derivative lineage;
- a journaled transaction with before state, mutation, readback, and rollback;
- full managed-scope reference and coverage audit.

Upgrading modes increases coverage. Never replace existing project UID or file UID merely because governance becomes stricter.

## Separate authorities from projections

- Registry: identity, owner, lifecycle, canonical path, and governed metadata.
- Home: stable entry point and links.
- Map: structure and relationship projection.
- Status: current operational state and blockers.
- Todo: executable work, dependencies, Definition of Done, and evidence references.
- Provenance: sources, imports, transformations, and external runtime pointers.
- Transaction journal: append-only mutation and rollback evidence.

Registry data controls identity. Home, Map, indexes, reports, and dashboards are discoverability projections; never use a generated view to silently overwrite its authority.

## Identity and ownership rules

- A UID is permanent identity. Rename, move, or archive keeps the same UID.
- A materially independent derivative or frozen release receives a new file UID linked to its parent.
- Each canonical file has exactly one owner. Reuse across projects by link or reference unless a documented derivative is needed.
- A hash proves bytes at a moment; it is not identity.
- Unknown ownership, UID, lineage, or canonical path is `REVIEW_REQUIRED`. Unsafe containment or collision is `BLOCKED`.

## Plan and audit

For a VGTREE-compatible Obsidian workspace, begin read-only:

```text
vgtree obsidian audit --vault <path> --mode core
vgtree obsidian plan --vault <path> --mode governed --output <outside-vault-plan.json>
```

Audit identity uniqueness, owner coverage, required navigation, registry/file agreement, hash readback, lineage integrity, unresolved references, transaction state, and root containment. Keep lifecycle states such as `ACTIVE` separate from audit outcomes such as `PASS`.

## Governed transaction contract

Before mutation, record exact targets, owner, authorization, preimage/hash, affected references, and rollback source. Apply bounded writes, verify bytes and links, then commit registry state. A registry must not point to an unverified filesystem result.

For moves, prefer destination creation/copy, hash verification, reference update, and readback. Source deletion is a separate destructive transaction. After rollback, verify bytes, registry, references, and discoverability; do not check only file existence.

VGTREE v1 audits and plans existing vaults but does not apply architecture changes to them. Do not reinterpret `scaffold` as authorization to reorganize an existing workspace.
