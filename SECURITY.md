# Security Policy

## Supported version

Security fixes are provided for the latest `1.x` release. Development branches are not a supported distribution channel.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for `scandium1102/vgtree`. Do not open a public issue containing exploit details, credentials, private vault content, or personal data.

Include the affected version, platform, minimal reproduction, impact, and any proposed mitigation. We will acknowledge a valid private report when maintainer capacity permits; this document does not promise a fixed response or remediation deadline.

## Security boundaries

- The core engine is local-first and performs no network requests.
- VGTREE does not store API keys or account credentials.
- Optional Obsidian live checks invoke a detected local CLI with `shell=False`.
- Obsidian audit inputs must resolve to bounded regular files inside the selected vault.
- Release builds install reviewed dependencies from a hash-locked file; the write-enabled publish job never checks out or executes repository source.
- Skills can influence agent behavior. Review untrusted skill changes before installation.
- VGTREE validates evidence structure and provenance fields, but domain tools remain responsible for the truth of their outputs.
- Local state and Vault directories are same-user trust boundaries; protect them with private filesystem permissions.

The pre-release security review and remediation record is published in [docs/security-review-v1.0.0.md](docs/security-review-v1.0.0.md).
