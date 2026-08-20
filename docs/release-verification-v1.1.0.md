# VGTREE 1.1.0 Release Verification

Date: 2026-08-21  
Tested source commit: `aee3a52`  
Local candidate status: **PASS**  
Public release status: **PENDING EXPLICIT AUTHORIZATION**

This record describes checks that were actually run. It does not claim that
GitHub Pages, GitHub Release, PyPI, or the OpenAI Plugins Directory already
contains VGTREE 1.1.0.

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

Two independent builds produced byte-for-byte identical payloads and checksum
manifests.

| Artifact | SHA-256 |
|---|---|
| `vgtree-1.1.0-py3-none-any.whl` | `88a694cd35b81c288cf2e9a929c765ade311666e7ad8221a56a5af2b9e04eceb` |
| `vgtree-1.1.0.tar.gz` | `41e6b37676cdb890eae59003fc6c09c3f1db6e77b0626588eb31efe3edbe8200` |
| `vgtree-plugin-1.1.0.zip` | `60f9f88c79b1f3738824b4a65b52d619927227d5b8aacf0f5a07214f96ea98e6` |
| `vgtree-skills-1.1.0.zip` | `0e921b769753fbf15c7379754a8a3b1e073d2f8e88de2dd794ed4fc5e86f4f4e` |
| `SHA256SUMS` | `ba1c413b8744220cae4d61f797c5653db11d8fbf31acde7e2d4c053f768c87f9` |

Archive inspection confirmed safe relative paths, no duplicate wheel entries,
regular-file/directory-only source distribution members, normalized metadata,
all four packaged schemas, and the intended Plugin and Skills-only layouts.

## Clean-room behavior

- A new environment installed the exact wheel with dependencies, reported
  `vgtree 1.1.0`, passed `pip check`, and exposed every documented command.
- From that wheel, Capability Map validation and compilation passed, state
  initialization passed, required coverage correctly returned `BLOCKED` before
  baseline evidence, and receipt validation passed with an exact digest.
- A separate new environment installed the exact source distribution, reported
  `vgtree 1.1.0`, passed package-data checks for the new schemas, and passed
  `pip check`.

Clean installation from the eventual GitHub Release and PyPI files remains a
post-publication readback gate. Local installation is not evidence that either
external service has published the files.

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

The following are not yet performed and must remain separate authorized actions:

1. Push the branch, create and review a pull request, pass remote CI, merge, and
   deploy/read back GitHub Pages.
2. Create the immutable `v1.1.0` tag, publish GitHub Release and PyPI, then read
   back assets, metadata, attestations, hashes, and clean installs.
3. Complete individual identity verification in the OpenAI Portal by the owner.
4. Create and scan the Skills-only Plugin draft using the exact release bundle.
5. Submit for review.
6. Publish after approval.

