# Obsidian read-only audit checklist

Use this checklist in SKILL_ONLY mode. Do not modify an existing vault.

- Resolve the intended vault root and confirm every inspected path remains inside it.
- Identify Home, Map, Status, Todo, project registry, and canonical project roots.
- In Core mode, review project UID uniqueness, canonical owner, discoverability, links, and rollback needs.
- In Governed mode, additionally review file UID uniqueness, raw-byte SHA-256 records, provenance, lineage, transaction state, and reference coverage.
- Distinguish filesystem inspection from live Obsidian validation.
- If the Obsidian CLI or a live session is unavailable, record `OBSIDIAN_LIVE_UNAVAILABLE`.
- Do not follow an audit finding with move, rename, rewrite, delete, scaffold-over-existing, or plugin installation.
- Report `runtime_mode=SKILL_ONLY`, `engine_validation=NOT_RUN`, and overall `REVIEW_REQUIRED`.

