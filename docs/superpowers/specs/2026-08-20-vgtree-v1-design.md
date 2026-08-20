# VGTREE v1.0 Product Design

Date: 2026-08-20
Product: VGTREE
Expansion: VEGA Governed Tree Runtime & Execution Engine
Tagline: Branch complex work into verifiable outcomes.
Descriptor: Verifiable tree workflows for AI agents and Obsidian.

## 1. Product intent

VGTREE turns a complex request into a governed tree of work, keeps primary outcomes ahead of attractive side quests, and allows completion only when integration and evidence gates pass. It is designed for AI coding agents, knowledge workers, and Obsidian users who want inspectable execution instead of opaque prompt chains.

VGTREE v1.0 is a local-first Python package, command-line tool, Agent Skills bundle, and skills-only OpenAI plugin. It does not include hosted services, telemetry, an MCP server, or a custom Obsidian plugin.

## 2. Principles

1. Simple work stays simple.
2. Risk signals can raise task complexity but never lower it.
3. Caller claims are inputs, not proof.
4. Completion is computed from state and evidence.
5. Every blocking or limitation decision is inspectable.
6. Public core remains generic; private governance belongs in adapters.
7. Existing vaults are read-only unless a future explicit apply feature is designed.

## 3. System shape

```text
Task JSON
   |
   v
Classifier --> Route Decision --> Tree Initializer
                                  |
                                  v
                         State + Branch DAG
                                  |
                      +-----------+-----------+
                      |                       |
                    Guard                 Verifier
                      |                       |
                      +-----------+-----------+
                                  |
                           Completion Gate
                                  |
                          Evidence-rich result
```

The Python API and CLI call the same engine. Skills teach agents when and how to call the engine. The plugin packages those skills. The Obsidian layer adds knowledge-architecture templates and validation without weakening the core gates.

## 4. Public interfaces

### Python

```python
from vgtree import VGTREEEngine

engine = VGTREEEngine()
decision = engine.classify(task_spec)
state = engine.initialize(task_spec)
report = engine.validate(state)
```

Core types:

- `TaskSpec`
- `WorkflowState`
- `Decision`
- `GuardResult`
- `ValidationReport`
- `VGTREEEngine`

Engine methods:

- `classify`
- `initialize`
- `next`
- `guard`
- `validate`
- `complete`
- `migrate_state`

### CLI

```text
vgtree classify --task TASK.json
vgtree init --task TASK.json --state STATE.json
vgtree next --state STATE.json
vgtree guard --state STATE.json --branch ID --activity NAME
vgtree validate --state STATE.json
vgtree complete --state STATE.json
vgtree migrate-state --input OLD.json --output NEW.json
vgtree obsidian audit --vault PATH --mode core|governed [--live]
vgtree obsidian plan --vault PATH --mode core|governed --output PLAN.json
vgtree obsidian scaffold --destination EMPTY_PATH --mode core|governed
```

All commands emit a stable JSON envelope with `status`, `code`, `message`, and `data`. Status and process exits are:

| Status | Exit |
|---|---:|
| `PASS` | 0 |
| `FAIL` | 1 |
| `REVIEW_REQUIRED` | 2 |
| `BLOCKED` | 3 |

## 5. Classification and routing

The classifier calculates a minimum task class from validated task signals. An explicit task class may raise but cannot lower the result.

- T0: one-step, reversible, low-risk response.
- T1: small bounded task with local verification.
- T2: multi-file or multi-surface work needing integration.
- T3: migration, release, architecture, or external-effect work.
- T4: high-risk, cross-system, destructive, or difficult-to-recover work.

Specialized routing requires a structured match record:

- `workflow_ref`
- `registered`
- `trigger_match`
- `context_match`
- `capability_match`
- `outcome_match`
- `safety_match`

Every field must pass. Otherwise T2-T4 tasks route to Tree execution.

## 6. State and evidence

Public state schema version: `2.0`.
Compatible workflow reference: `WF-VEGA-TREE@1.0`.
New field: `engine_version`.

State is stored under `.vgtree/tasks` by default. The migration command accepts the current internal state schema `1.1` and emits `2.0` without overwriting the input.

Branches form a directed acyclic graph. Validation rejects missing dependencies, self-dependencies, cycles, invalid priorities, and deferred priorities on primary branches.

Evidence records include:

- evidence type
- subject
- command or method
- timestamp
- outcome
- digest or reference when applicable

Blocked branches require a blocking reason and evidence. Accepted limitations require an explicit acceptance record, scope, consequence, owner, and evidence.

## 7. State machine

Legal high-level phases:

```text
mission_understanding
  -> outcome_definition
  -> breadth_mapping
  -> branch_execution
  -> integration
  -> verification
  -> complete
```

The engine may return `REVIEW_REQUIRED` or `BLOCKED` without advancing. It never accepts a caller-provided gate boolean as final truth. Gates are derived from branch state, dependencies, evidence, and phase requirements.

## 8. Persistence and concurrency

- Atomic write through a temporary sibling file followed by `os.replace`.
- Exclusive lock file creation prevents two writers from mutating the same task.
- Lock collisions return `BLOCKED`; stale-lock recovery is explicit and never automatic in v1.
- No shell invocation in the engine.
- Optional Obsidian CLI checks use argument arrays with `shell=False`.

## 9. Obsidian integration

VGTREE supports two modes:

### Core mode

- project or owner UID
- registry
- Home, Map, Status, and Todo surfaces
- links and discoverability checks

### Governed mode

Core mode plus:

- file UID
- content hash
- provenance and lineage
- transaction and readback evidence

`audit` and `plan` are read-only. `scaffold` writes only to a new or empty destination. V1 never mutates an existing vault. `--live` returns `BLOCKED` when Obsidian is unavailable rather than pretending live validation occurred.

## 10. Skills and plugin

The skills-only plugin contains six composable skills:

1. `using-vgtree`
2. `planning-tree-work`
3. `executing-tree-work`
4. `verifying-tree-work`
5. `governing-knowledge-architecture`
6. `building-obsidian-workspaces`

Each skill has a concise trigger description, executable instructions, and representative evaluation scenarios. The plugin does not declare MCP servers, apps, hooks, or network access.

## 11. Repository layout

```text
vgtree/
  .agents/plugins/marketplace.json
  .github/workflows/
  plugins/vgtree/.codex-plugin/plugin.json
  plugins/vgtree/skills/
  src/vgtree/
  schemas/
  templates/obsidian/
  tests/
  evals/
  docs/
  pyproject.toml
  README.md
  README.zh-TW.md
  LICENSE
  SECURITY.md
  PRIVACY.md
  TERMS.md
  SUPPORT.md
  CHANGELOG.md
```

## 12. Release contract

- Version: `1.0.0`
- License: MIT
- GitHub target: `scandium1102/vgtree`
- Canonical documentation: English
- Quick start: Traditional Chinese and English
- Git install target: `pip install git+https://github.com/scandium1102/vgtree.git@v1.0.0`
- No PyPI publication in v1.0
- No telemetry

Release requires unit, integration, CLI, schema, migration, Obsidian, plugin, skill-eval, packaging, clean-room install, security, privacy, and public-content checks.

## 13. Deferred scope

- MCP server
- hosted execution service
- web dashboard
- telemetry
- automatic mutation of existing Obsidian vaults
- custom Obsidian plugin
- multi-user coordination service
