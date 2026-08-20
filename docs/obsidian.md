# Obsidian Guide

VGTREE supports static audit, read-only planning, safe starter scaffolding, and optional live CLI confirmation.

## Audit an existing vault

```bash
vgtree obsidian audit --vault /path/to/vault --mode core
```

Audit checks required surfaces, project UID agreement, Home discoverability, YAML frontmatter, and registries. Governed mode additionally checks file UID and raw-byte hash agreement.

To generate a plan, place its new output outside the vault:

```bash
vgtree obsidian plan --vault /path/to/vault --mode governed --output /outside/vault/plan.json
```

The plan is advisory and read-only. VGTREE v1 has no existing-vault `apply` command.

## Create a starter

```bash
vgtree obsidian scaffold --destination /path/to/new-vault --mode governed
```

The destination must be new or empty. VGTREE renders into a temporary sibling, audits the result, and moves it into place only after the audit passes. A non-empty destination returns `BLOCKED` and remains unchanged.

Core creates Home, Project Map, Status, Todo, and a project registry. Governed adds file UIDs and hashes, Provenance, Transactions, and a file registry.

## Live check

Open the exact vault in Obsidian first:

```bash
vgtree obsidian audit --vault /path/to/vault --mode core --live
```

When the local CLI cannot confirm a live session, VGTREE returns `BLOCKED / OBSIDIAN_LIVE_UNAVAILABLE` and does not claim live validation. Static results remain available in the JSON data.

Live CLI response does not replace representative checks for links, backlinks, embeds, attachments, properties, search, Canvas/Bases, third-party plugins, and restart persistence.

## Existing-vault safety

Do not use scaffold as an apply mechanism. Any future migration of existing notes needs a separately authorized snapshot, collision policy, transaction journal, reference plan, idempotency proof, and tested rollback.
