# VGTREE v1.0.0 security review

Review date: 2026-08-20

## Scope and result

The full pre-release repository was reviewed across source code, schemas, Skills, Obsidian integration, tests, packaging, and GitHub workflows. The initial review found no critical or high-severity issue. It reported three medium- and three low-severity issues; all six were remediated before v1.0.0 publication.

## Remediations

| Initial finding | Resolution | Regression evidence |
|---|---|---|
| Command-adjacent identifiers could carry shell metacharacters into copied Skill commands | Identifiers now use a bounded safe-character grammar; Skills require argument-array execution and treat task content as untrusted data | Schema and Skill contract tests |
| Release build and repository write permission shared one mutable job | Release build is read-only, dependencies are exact and hash locked, Actions are pinned to full SHAs, and only verified artifacts enter the write-enabled job | CI policy tests and clean locked build |
| State validation trusted stored semantic claims | Validator recomputes the minimum task class and enforces route, phase/history, branch, integration, and final-evidence coherence | Semantic state regression tests |
| State read-modify-write and first-write paths could race | The store locks the full transaction and uses an atomic non-overwriting create path | Deterministic concurrency and racing-destination tests |
| Obsidian audit could follow links or read outside the selected vault | Required inputs must resolve inside the vault, cannot be links, must be regular files, and are capped at 4 MiB | Link-containment and oversized-file tests |
| Recursive DAG validation could exhaust the Python stack | DAG validation is iterative and branch/dependency counts are bounded | Maximum-depth and branch-bound tests |

## Residual boundaries

- VGTREE validates control-plane state and evidence structure; it cannot prove that a caller's domain evidence is truthful.
- Optional live Obsidian validation requires an available and responsive local Obsidian CLI. Static audits remain available without it.
- Installed Skills are executable agent instructions and should be reviewed like code before accepting third-party modifications.
- No telemetry, hosted execution, MCP server, automatic mutation of existing vaults, or credential storage is included in v1.0.0.

Dependency audit and release smoke-test results are recorded in [release-verification-v1.0.0.md](release-verification-v1.0.0.md).
