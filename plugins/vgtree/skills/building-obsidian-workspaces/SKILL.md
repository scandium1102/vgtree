---
name: building-obsidian-workspaces
description: Use when auditing an existing Obsidian vault or creating a new VGTREE starter workspace with safe Core/Governed selection, read-only planning, live validation, and no-loss boundaries.
---

# Building Obsidian Workspaces

First decide whether the target is an existing vault or a new workspace. The commands are intentionally different.

## Existing vault: audit and plan only

Start with Core unless the user has explicitly chosen the additional UID/hash/transaction maintenance of Governed mode.

```text
vgtree obsidian audit --vault <existing-vault> --mode core
vgtree obsidian plan --vault <existing-vault> --mode governed --output <outside-vault-plan.json>
```

The plan output must be new and outside the audited vault. Review missing Home, Map, Status, Todo, project registry, file UID, hash, and provenance findings without changing note bytes.

VGTREE v1 does not apply, move, rename, rewrite, or delete files in an existing vault. It does not have an `apply` command. Never simulate apply by pointing `scaffold` at the vault, copying generated files over it, or manually following a plan without a separately designed and authorized migration transaction.

## New workspace: scaffold

Use only a new or empty destination:

```text
vgtree obsidian scaffold --destination <new-or-empty-path> --mode core
vgtree obsidian audit --vault <new-path> --mode core
```

Choose `governed` at scaffold time when every starter Markdown surface should have a file UID and registry-backed raw-byte hash, plus provenance and transaction surfaces. Scaffold rejects non-empty destinations and never overwrites them.

The starter creates navigation and governance surfaces; it does not install an Obsidian plugin, enable third-party plugins, or configure sync.

## Live Obsidian validation

Static audit proves filesystem structure. When a live claim is required, open the exact vault in Obsidian first, then run:

```text
vgtree obsidian audit --vault <path> --mode core --live
```

If Obsidian CLI is missing or no live session responds, preserve the static findings and report `BLOCKED` with `OBSIDIAN_LIVE_UNAVAILABLE`. Never relabel a static audit as live validation.

After a live pass, still check representative notes, wikilinks, backlinks, embeds, attachments, properties, Bases/Canvas when used, search, and restart persistence with appropriate Obsidian tools. VGTREE's starter audit does not claim compatibility with every third-party plugin.

## No-loss and rollback boundary

- Existing-vault audit and plan are read-only, so they need no content rollback.
- A scaffold is additive and isolated. Retain its returned file manifest.
- Do not delete a scaffold automatically if later work fails; it may have been edited after creation.
- Any future existing-vault migration needs its own snapshot, byte/hash inventory, collision policy, transaction journal, reference update plan, explicit apply authorization, and tested rollback.

Never claim the user's original notes were preserved by an apply operation, because VGTREE v1 performs no such operation.
