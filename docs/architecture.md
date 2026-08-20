# Architecture

VGTREE is a thin control plane. It routes work, persists state, enforces branch and phase rules, and computes structural completion gates. Domain tools remain responsible for implementation, testing, deployment, security, and authoritative remote readback.

## Components

```text
Task JSON
  -> schema validation
  -> deterministic classifier
  -> direct | registry-verified specialized | tree route
  -> initialized branch DAG and persistent state
  -> guard / evidence / legal branch transitions
  -> integration evidence
  -> final-verification evidence
  -> computed completion result
```

The CLI and Python API use the same engine. The six Agent Skills teach routing and operational behavior without duplicating engine logic. The OpenAI plugin packages Skills only. The Obsidian layer audits or scaffolds knowledge surfaces without weakening core evidence gates.

## Classification

File count establishes an initial complexity floor. Migration, project-scale, external-effect, and cross-system signals raise the floor to T3. Destructive or irreversible signals raise it to T4. An explicit class can raise but never lower the computed result.

A specialized workflow is selected only when its reference appears in an explicit active/verified registry and all trigger, context, capability, outcome, and safety match flags are true.

## State model

State schema 2.0 keeps the compatibility reference `WF-VEGA-TREE@1.0` and adds `engine_version`. Branches form a DAG and store kind, priority, status, dependencies, optional Definition of Done, evidence requirements, stop condition, and typed evidence.

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

## Result contract

Every operational command emits JSON with `status`, `code`, `message`, and `data` and maps status to exit `0/1/2/3` for `PASS/FAIL/REVIEW_REQUIRED/BLOCKED`.

## Deliberate v1 exclusions

No MCP server, hosted runner, telemetry, web dashboard, custom Obsidian plugin, automatic existing-vault mutation, or multi-user coordination service is included.
