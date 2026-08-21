# VGTREE 1.1.0 Release Verification

- Date: 2026-08-21
- Tagged release commit: `77121a03ff506ca1c5d609cf2673b593f4abbb59`
- Local candidate status: **PASS WITH PUBLIC-BYTE QUALIFICATION**
- Public release status: **IN PROGRESS** — GitHub Release and Pages readback
  passed; PyPI and OpenAI directory publication remain external gates

This record describes checks that were actually run and distinguishes completed
public readback from remaining external gates. It does not claim that PyPI or
the OpenAI Plugins Directory contains VGTREE 1.1.0 until those readbacks pass.

## Source and deterministic validation

- Full unit suite: **190 tests passed, 0 failed**.
- Python bytecode compilation: `src`, `scripts`, and `tests` passed.
- Five deterministic VGTREE 1.1 evaluation families passed.
- OpenAI submission validator passed with five positive cases, three negative
  cases, five starter prompts, and six Skills.
- Repository private-marker, credential-pattern, workflow-permission, and
  action-pin tests passed as part of the full suite.
- Working-tree and repository diff whitespace checks passed.

## Plugin and Skill validation

- The official Plugin validator passed on the source Plugin.
- The official Skill validator passed all six Skills.
- The same validators passed again against the extracted release Plugin ZIP.
- The extracted Plugin contained 25 regular files.
- An Engine-free validation with an empty executable search path returned:
  `runtime_mode=SKILL_ONLY`, `engine_validation=NOT_RUN`,
  `installed_software=false`, and `overall_status=REVIEW_REQUIRED`.

## Dependencies and package metadata

- The exact hash-locked release environment installed successfully.
- `pip check` reported no broken requirements.
- `pip-audit 2.10.1` reported no known vulnerabilities in
  `requirements/release.txt`.
- `twine 7.0.0 check` passed the wheel and source distribution.
- The dedicated security diff review found no reportable vulnerability; see
  [Security Review](security-review-v1.1.0.md).

## Release artifacts

The canonical public artifacts are the outputs built from the clean `v1.1.0`
tag checkout by GitHub Actions. Their `SHA256SUMS` manifest validates all four
payloads, and a fresh public download produced the following byte digests:

| Artifact | SHA-256 |
|---|---|
| `vgtree-1.1.0-py3-none-any.whl` | `b1adb3b9353fd96a787b466f1bd85319da5506c1a75e762e3aaa1720544afc0a` |
| `vgtree-1.1.0.tar.gz` | `e8ed6b63b605be7127f73ba1584b6a290c9487ea9aff0c283280da7b3d3f2363` |
| `vgtree-plugin-1.1.0.zip` | `de86e551c152cdc21d895ca47f85b97801984b3e11f06de66007a703a31a4dd5` |
| `vgtree-skills-1.1.0.zip` | `d8cb8b2ebed579fb5f474b37498624620bacf9ac77ffb8787014e722ab5e5d45` |
| `SHA256SUMS` | `114cfccb0c256805a287338896670199ff9edbd177e405e09abce4e4c4be06c2` |

The earlier Windows worktree verification repeated successfully inside that
worktree but included mixed working-copy line endings, so its hashes were not
used as public-byte authority. A separate clean checkout of the immutable tag
reproduced the two Plugin ZIPs byte-for-byte. Wheel and sdist reproducibility
is scoped to the pinned release build environment; the public files themselves
passed manifest verification, metadata validation, and clean installation.

Archive inspection confirmed safe relative paths, no duplicate wheel entries,
regular-file/directory-only source distribution members, normalized metadata,
all four packaged schemas, and the intended Plugin and Skills-only layouts.

## Clean-room behavior

- A new environment installed the exact public GitHub Release wheel with dependencies, reported
  `vgtree 1.1.0`, passed `pip check`, and exposed every documented command.
- From that wheel, Capability Map validation and compilation passed, state
  initialization passed, required coverage correctly returned `BLOCKED` before
  baseline evidence, and receipt validation passed with an exact digest.
- A separate new environment installed the exact source distribution, reported
  `vgtree 1.1.0`, passed package-data checks for the new schemas, and passed
  `pip check`.

The downloaded public wheel and sdist also passed `twine check`; the downloaded
Plugin ZIP passed the official Plugin validator and all six official Skill
validators. Clean installation from PyPI remains a separate post-publication
readback gate.

## Website and publishing controls

- Automated site tests passed local-only assets, internal links, policy copy,
  responsive CSS, semantic structure, and WCAG AA contrast calculations.
- Browser checks covered 360, 768, and 1440 pixel widths, English and
  Traditional Chinese pages, keyboard focus, overflow, console errors, and the
  privacy and terms pages.
- Pages and release workflows separate read-only builds from write-capable
  deployment jobs, use least privilege, and pin every action to a full commit
  SHA.
- PyPI publication is tag-gated, uses the protected `pypi` environment, and
  receives only short-lived OIDC authority; no PyPI token is stored.

## Deliberate external gates

Completed public gates:

1. The release branch, PR CI, merge, and main CI passed.
2. GitHub Pages deployed and all six routes/assets passed anonymous exact-byte
   readback.
3. The immutable `v1.1.0` tag and GitHub Release were published; all five
   public assets passed inventory and checksum readback.

Remaining external gates:

1. Configure the PyPI pending Trusted Publisher, rerun the failed PyPI job from
   the same release run, and verify metadata, attestations, hashes, and a clean
   install.
2. Complete individual identity verification in the OpenAI Portal by the owner.
3. Create and scan the Skills-only Plugin draft using the exact public Plugin
   bundle, submit it for review, and publish after approval.
