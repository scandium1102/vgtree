# executing-tree-work evaluation: blocked primary branches

Date: 2026-08-20

## Baseline

The agent correctly prioritized primary work and refused to claim completion, but invented non-schema states such as `BLOCKED_PERMISSION`, `DONE_VERIFIED`, `DEFERRED_NOT_REQUIRED`, and `PARTIAL_BLOCKED`. Its evidence ledger and transition controls were conceptual rather than executable.

## With the skill

The agent used `validate`, `next`, `guard`, `set-branch`, and `record-evidence`; kept the unverified dependency from entering `IN_PROGRESS`; retained secondary work as deferred; and treated the state file as the ledger. It removed every invented state and separated branch success from overall completion.

## Refinement

The first after-skill answer omitted the required `--blocked-reason` CLI argument. The skill was tightened with an exact blocker command so future executions cannot confuse narrative reason text with a valid state mutation.

Verdict: PASS after command refinement.
