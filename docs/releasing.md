# Releasing VGTREE

This runbook prepares a release; it does not grant authority to publish one. Follow `docs/release-authorization-gates.md` and obtain the release owner's action-time approval for each external-effect gate.

## One-time repository setup

1. Create the GitHub environment `pypi` and configure a required reviewer so the OIDC publishing job waits for human approval. Restrict deployment branches or tags to the release policy supported by the repository plan.
2. In PyPI, configure a pending or existing-project Trusted Publisher for:
   - owner: `scandium1102`
   - repository: `vgtree`
   - workflow: `release.yml`
   - environment: `pypi`
3. Do not create or store a PyPI API token. The publish job has only `id-token: write` and uses the short-lived credential issued for the matching workflow identity.

A pending publisher does not reserve the project name. Confirm that the `vgtree` distribution is still available immediately before the first release; if another project owns it, stop with `BLOCKED` and do not silently rename the product.

## Candidate verification

From a clean release checkout, use the hash-locked release dependencies, run the complete test and validator matrix, then build:

```bash
python -m build --no-isolation
python scripts/build_release_bundles.py --dist dist --version 1.1.0
cd dist && sha256sum -c SHA256SUMS
```

The directory must contain exactly the wheel, sdist, `vgtree-plugin-1.1.0.zip`, `vgtree-skills-1.1.0.zip`, and `SHA256SUMS`. Install the wheel and sdist separately in clean environments. Extract the plugin bundle and rerun the official Plugin validator plus every Skill validator before upload.

## Immutable publication

After main-branch CI and deployed Pages readback pass, obtain the separate version-release authorization and create `v1.1.0` at the approved commit. The tag-triggered workflow builds once, publishes the five GitHub Release assets, and sends only the wheel and sdist to PyPI through the protected environment.

After a successful release, read back the GitHub asset hashes, PyPI metadata, Trusted Publisher attestations, and clean installations from both public sources. Then freeze the evidence in the release verification record.

Once public, never move, delete, or recreate the tag. If containment is needed, yank the PyPI version, restore Pages from the last known-good SHA, pause the directory listing when supported, and publish a fixed `1.1.1`; do not overwrite `1.1.0`.
