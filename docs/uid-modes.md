# UID and Knowledge Architecture Modes

VGTREE uses one authority model with two strengths.

## Core mode

Core is the default for ordinary personal and project knowledge. It requires:

- stable project UID;
- one canonical owner/root;
- project registry;
- Home, Map, Status, and Todo discoverability;
- links to real outcomes and evidence;
- rollback context for destructive or multi-file operations.

## Governed mode

Governed keeps Core identity and adds:

- file UID for every managed Markdown surface;
- raw-byte SHA-256 stored in a file registry;
- provenance and parent/derivative lineage surfaces;
- transaction, readback, and rollback records;
- managed-scope coverage and reference audit.

Moving or renaming a file does not change its UID. A materially independent derivative or frozen release receives a new UID linked to its parent. A hash proves bytes at a moment and never replaces identity.

Upgrading Core to Governed expands coverage without replacing existing UIDs. Unknown ownership, UID, lineage, or canonical path is `REVIEW_REQUIRED`; unsafe containment or collision is `BLOCKED`.

## Authority versus projection

Registries control identity, owner, lifecycle, and canonical path. Home, Map, indexes, reports, and dashboards are projections for discoverability. Generated projections must not silently overwrite their authority.

The starter's identifiers are examples for a new workspace. Integrating an existing governance system requires an explicit adapter and migration plan; do not copy its private namespaces into public VGTREE core.
