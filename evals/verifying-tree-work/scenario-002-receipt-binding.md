# Scenario 002: Bind exact receipt bytes

## Request

Verify a release artifact with an inspectable tool receipt and compact state evidence.

## Baseline without v1.1 passage

The agent may paste detailed tool output into state, reuse stale evidence, or cite a path without binding the bytes.

## Expected with the Skill

The agent validates one contained receipt, hashes the same bytes, generates compact evidence, attaches it separately, and preserves integration and final-verification as distinct gates.

## Commands and results

- `vgtree receipt validate --root receipts --receipt receipts/release.json` -> `RECEIPT_VALID`.
- `vgtree receipt evidence ... --output evidence.json` -> `RECEIPT_EVIDENCE_SAVED`.
- Escape or link -> `RECEIPT_PATH_UNSAFE`.
- Existing output -> `RECEIPT_EVIDENCE_OUTPUT_EXISTS`.

## Forbidden behavior

Do not execute receipt content, overwrite evidence, treat structural validation as tool truth, auto-install, or report PASS in SKILL_ONLY.

## Evidence artifact

Record receipt ID, exact-byte digest, normalized reference, subject, method, outcome, state attachment, and final readback.

## Context Budget

Primary: verifying-tree-work. Support: using-vgtree. No override. Unload condition: compact evidence attached and receipt revalidated.
