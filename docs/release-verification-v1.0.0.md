# VGTREE v1.0.0 release verification

Verification date: 2026-08-20

This record captures the public, reproducible pre-release checks. It contains no private Vault content, credentials, or workstation-specific source paths.

## Verified checks

| Check | Result |
|---|---|
| Python unit and policy suite | PASS — 103 tests |
| Python bytecode compilation | PASS |
| Plugin manifest validator | PASS |
| Six individual Skill validators | PASS |
| Release dependency install with `--require-hashes` | PASS |
| `pip check` in isolated build environment | PASS |
| `pip-audit 2.10.1` against `requirements/release.txt` | PASS — no known vulnerabilities found at verification time |
| Wheel and sdist build with `--no-isolation` | PASS |
| Clean wheel install and `vgtree --help` | PASS |
| Governed Obsidian scaffold from installed wheel | PASS |
| Static governed Obsidian audit | PASS |
| Obsidian live audit without a confirmed local session | BLOCKED as designed, exit code 3, no false PASS |
| Public-text private-path and secret-pattern checks | PASS |

## Release controls

- GitHub Actions are pinned to full commit SHAs.
- The release build job has read-only repository permission and disables persisted checkout credentials.
- Release dependencies are exact and SHA-256 locked.
- The write-enabled release job receives only artifacts, verifies `SHA256SUMS`, and does not check out or install repository code.
- Tag `v1.0.0` must match the Python package version before artifacts are published.

Artifact SHA-256 values are generated again from the final tagged build and attached as `SHA256SUMS` to the GitHub release. A local pre-publication build is intentionally not treated as the remote release artifact.

## Reproduce

```bash
python -m pip install --require-hashes -r requirements/release.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m unittest discover -s tests -v
python -m compileall -q src
python -m build --no-isolation
```
