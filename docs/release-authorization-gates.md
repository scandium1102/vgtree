# VGTREE release authorization gates

This contract separates local implementation from external publication. It is part of the VGTREE 1.1 release candidate and does not itself authorize an external action.

## Local authority

The approved VGTREE 1.1 productization plan authorizes reversible implementation, local builds, local validation, and preparation of publication materials in `codex/vgtree-v1.1-release`.

The current local workflow must not infer authority for GitHub writes, identity actions, PyPI publication, OpenAI review submission, or final directory publication.

## Action-time gates

| Gate | Exact external effect | Required owner action |
|---|---|---|
| GitHub integration | Push the branch, create the PR, merge it, and deploy Pages | The release owner explicitly authorizes the bounded GitHub integration batch after local verification |
| Version release | Create immutable tag `v1.1.0`, GitHub Release, and PyPI `1.1.0` | The release owner explicitly authorizes the exact tag after integrated CI and Pages readback |
| Individual verification | Upload or submit identity material in the OpenAI Portal | The release owner performs this personally; the agent does not read, handle, or upload identity documents |
| Skills-only draft | Create the draft, upload the exact verified bundle, and enter listing data | The release owner explicitly authorizes Portal draft creation and upload |
| Review submission | Press `Submit for Review` | The release owner gives fresh action-time authorization after the Portal scan and field readback |
| Directory publication | Press `Publish` after approval | The release owner gives a separate fresh authorization after approval readback |

Login state, an approved RFC, an earlier gate, or a successful local test does not imply a later gate.

## Non-overwriting rollback

- Never move or recreate the `v1.1.0` tag.
- If PyPI needs containment, yank `1.1.0` and ship a fixed `1.1.1`; do not overwrite the distribution.
- Restore Pages by redeploying the last known-good source SHA.
- Pause or unpublish the OpenAI listing when the Portal supports it, then submit a corrected immutable bundle.
- Preserve the failed artifact, checksum, workflow run, and public readback as evidence.

## Current readback

At the time this contract was added, work remained local: no feature-branch push, PR, merge, Pages deployment, `v1.1.0` tag, GitHub Release, PyPI publication, OpenAI identity submission, review submission, or directory publication had been performed by this release workflow.
