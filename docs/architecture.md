# Architecture

VGTREE is a thin control plane. It routes work, persists state, enforces branch and phase rules, and computes structural completion gates. Domain tools remain responsible for implementation, testing, deployment, security, and authoritative remote readback.

## Components

```text
Capability Map (optional)
  -> deterministic task compilation
Task JSON
  -> schema validation
  -> deterministic classifier
  -> direct | registry-verified specialized | tree route
  -> initialized branch DAG and persistent state
  -> wide-pass coverage / one-way deep transition
  -> guard / receipts / evidence / legal branch transitions
  -> integration evidence
  -> final-verification evidence
  -> computed completion result
```

The CLI and Python API use the same engine. The six Agent Skills teach routing and operational behavior without duplicating engine logic. In ENGINE mode they use deterministic CLI gates. In SKILL_ONLY mode they use shared schemas/templates for useful planning and review, report `engine_validation=NOT_RUN`, and cannot claim overall `PASS`. The OpenAI plugin packages Skills only. The Obsidian layer audits or scaffolds knowledge surfaces without weakening core evidence gates.

## Classification

File count establishes an initial complexity floor. Migration, project-scale, external-effect, and cross-system signals raise the floor to T3. Destructive or irreversible signals raise it to T4. An explicit class can raise but never lower the computed result.

A specialized workflow is selected only when its reference appears in an explicit active/verified registry and all trigger, context, capability, outcome, and safety match flags are true.

## State model

State schema 2.0 remains the VGTREE 1.0-compatible path for normal tasks and Capability Maps with policy `OFF`. State 2.1 is opt-in for `ADVISORY` and `REQUIRED` maps. It binds the map digest and immutable branch coverage fields to the embedded task and adds a branch-execution substate:

```text
WIDE -> DEEP
```

Coverage is recomputed from exact passing baseline evidence. `REQUIRED` blocks the transition; incomplete `ADVISORY` needs a reasoned override. Baseline evidence never substitutes for branch acceptance, integration, or final-verification evidence.

Legal phases are:

```text
mission_understanding
-> outcome_definition
-> breadth_mapping
-> branch_execution
-> integration
-> verification
-> complete
```

State changes are written atomically through a temporary sibling file and `os.replace`. An exclusive lock prevents concurrent writers. Lock recovery is explicit; VGTREE v1 does not silently remove a lock that might belong to another process.

## Evidence and trust boundary

Passing evidence requires a SHA-256 digest or durable reference. A verified branch requires passing evidence. Integration and final-verification are separate global evidence types.

VGTREE verifies schema, provenance fields, state consistency, and gate presence. It cannot independently prove that a caller fabricated neither a command result nor a remote reference. Skills therefore require evidence to come from the actual domain tool and exact final subject.

Detailed Tool Receipts are immutable sidecar JSON files below an explicit receipt root. VGTREE rejects path escape, links, non-files, and files over 4 MiB, hashes the exact bytes read, and generates compact evidence carrying that digest and reference. Receipt fields remain untrusted data and are never executed. Structural validation and digest binding do not prove that the producing tool told the truth. Local state, receipt, and vault directories are same-user trust boundaries rather than hostile multi-user isolation.

## Result contract

Every operational command emits JSON with `status`, `code`, `message`, and `data` and maps status to exit `0/1/2/3` for `PASS/FAIL/REVIEW_REQUIRED/BLOCKED`.

## Deliberate v1.1 exclusions

No MCP server, hosted runner, telemetry, web dashboard, custom Obsidian plugin, automatic existing-vault mutation, or multi-user coordination service is included.
