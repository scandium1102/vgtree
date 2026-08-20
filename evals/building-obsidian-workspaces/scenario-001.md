# building-obsidian-workspaces evaluation: existing vault

Date: 2026-08-20

## Baseline

The agent chose a cautious audit/staging/rollback strategy, but proposed a later reviewed apply even though VGTREE v1 intentionally has no existing-vault mutation surface.

## With the skill

The agent selected Core by default, limited an existing vault to read-only audit and outside-vault plan output, reserved scaffold for a new or empty destination, and required the exact vault to be open before `--live`. It correctly mapped unavailable live validation to `BLOCKED / OBSIDIAN_LIVE_UNAVAILABLE` while preserving static results.

The central correction was explicit: VGTREE v1 ends at audit and plan for existing vaults. A staged apply, scaffold-over-existing, or manual plan execution is outside the supported and authorized product boundary.

Verdict: PASS.
