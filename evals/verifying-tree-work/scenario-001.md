# verifying-tree-work evaluation: stale release evidence

Date: 2026-08-20

## Baseline

The agent correctly refused completion and described strong release, limitation-owner, and anonymous-readback gates. The result was still a prose status taxonomy rather than a computed VGTREE completion decision.

## With the skill

The agent returned `REVIEW_REQUIRED`, bound fresh integration and final evidence to one exact release subject, preserved stale evidence, required authoritative anonymous GitHub readback, and used `validate`, `record-evidence`, `complete`, and post-completion state readback.

## Refinement

The first after-skill answer invented an evidence field named `digest_or_reference`. The skill was tightened with a complete schema-valid evidence example and an explicit prohibition on that alias.

Verdict: PASS after evidence-field refinement.
