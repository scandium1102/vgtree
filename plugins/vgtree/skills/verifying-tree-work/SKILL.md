---
name: verifying-tree-work
description: Use when agents must verify a multi-branch VGTREE outcome with fresh integration evidence, limitation ownership, artifact integrity, external readback, and computed completion gates.
---

# Verifying Tree Work

Verification asks whether the requested outcome is proven now, on the exact integrated state. It does not reward effort or branch count.

## Establish the verification subject

Identify the exact commit, artifact, schema, vault snapshot, deployment, or release being verified. Evidence from another subject or older integrated state is stale even if it once passed.

Run `vgtree validate --state <state.json>`. Inspect every primary branch's Definition of Done and evidence requirements. A `VERIFIED` label without matching passing evidence is a defect, not proof.

## Recheck branch and limitation integrity

- Confirm each required primary branch is `VERIFIED` or has a valid `ACCEPTED_LIMITATION`.
- An accepted limitation needs scope, consequence, owner, `accepted_at`, and evidence. Missing ownership is `REVIEW_REQUIRED`.
- Confirm dependency and integration subjects resolve to the same intended outcome.
- Preserve failed and stale evidence; add fresh evidence instead of rewriting history.

## Produce fresh integration evidence

Run the relevant integrated tests, link/readback checks, artifact checksums, security/privacy checks, and worktree disposition against the exact subject. Use the schema's exact fields, not invented aliases:

```json
{
  "id": "integration-final-subject",
  "type": "integration",
  "subject": "exact commit, tag, artifact, or snapshot",
  "method": "fresh integrated command and readback",
  "timestamp": "2026-08-20T00:00:00Z",
  "outcome": "PASS",
  "digest": "sha256:<hex>",
  "reference": "durable local or remote evidence reference"
}
```

`digest` and `reference` are separate optional fields; never invent `digest_or_reference`.

After branch gates pass:

```text
vgtree next --state <state>
vgtree record-evidence --state <state> --evidence <integration.json>
vgtree next --state <state>
```

The integration evidence type must be `integration` with outcome `PASS` before the engine enters verification.

## Verify external effects separately

For releases, deployments, public pages, messages, or account mutations, read the result back from the authoritative remote system. When public visibility matters, add anonymous or unauthenticated readback where practical. Verify the final URL, status, commit/tag, asset list, size, and digest rather than relying on the write response.

Do not claim an external effect occurred when authorization, execution, review, or readback is still pending.

## Final completion gate

Create fresh `final-verification` evidence tied to the exact integrated subject, then run:

```text
vgtree record-evidence --state <state> --evidence <final-verification.json>
vgtree validate --state <state>
vgtree complete --state <state>
vgtree validate --state <state>
```

Claim overall completion only when:

- `vgtree complete` exits `0` with `status=PASS` and `code=COMPLETE`;
- state readback shows `phase=complete`;
- the evidence is fresh and bound to the final subject;
- all authorized external effects have authoritative readback;
- no unresolved primary blocker, unsafe worktree change, or unowned limitation remains.

Otherwise report the narrow completed branches and the overall `FAIL`, `REVIEW_REQUIRED`, or `BLOCKED` result exactly.
