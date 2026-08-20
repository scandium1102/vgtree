# VGTREE 1.1.0 Security Review

Date: 2026-08-21  
Result: **No reportable security findings**

## Scope

The security diff review covered the complete VGTREE 1.1 implementation from
`6a9aef625af60b2512ee0171bc9f7550a9680d8f` through
`e8f1ed6b1759f5a70700781945957535672c6d2d`.

The review included a repository-specific threat model, 45 security-relevant
source and workflow items, and supporting review of the six Skills, tests,
Plugin assets, release workflows, archive builder, state persistence, receipts,
and local Obsidian operations. It considered path containment, archive paths,
symlinks, bounded input, state and receipt integrity, lock ownership, secret
exposure, GitHub Actions permissions, immutable action pins, OIDC publishing,
and the no-network/no-telemetry product boundary.

Changes after the scanned head comprise trailing blank-line normalization,
example receipt digest rebinding, and verification documentation/tests only. A
final diff review and the complete test matrix confirmed that they do not
change runtime, workflow, or publishing semantics.

## Findings

No release-blocking or reportable vulnerability was confirmed.

Two low-severity local robustness risks remain documented:

- An Obsidian audit validates a resolved regular file and later opens it by
  pathname. A hostile process with the same user account and concurrent access
  to that vault could attempt a path-swap race.
- Lock cleanup reads a lock token and then removes the lock path. A hostile
  process with the same user account and write access to the state directory
  could attempt a replacement race in that small interval.

These risks do not cross VGTREE's documented local same-user trust boundary and
do not justify delaying 1.1.0. They should be reconsidered if VGTREE later adds
multi-user, privileged, network, or hosted execution.

## Review constraints

- The optional TAC display connector was not connected, so its advisory result
  was not available. This did not reduce repository or artifact review coverage.
- Delegated security workers were unavailable under the active execution
  policy. The primary reviewer completed every inventory item directly.
- This review does not claim that structural evidence proves domain truth.
  VGTREE still requires the caller or an appropriate domain tool to establish
  that evidence is substantively correct.
