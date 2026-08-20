<p align="center">
  <img src="plugins/vgtree/assets/logo.svg" alt="VGTREE" width="520">
</p>

# VGTREE

Branch complex work into verifiable outcomes.

VGTREE (VEGA Governed Tree Runtime & Execution Engine) is a local-first Python engine, CLI, and skills-only OpenAI plugin for planning, executing, and verifying complex work. It adds persistent branch state, dependency guards, evidence-gated completion, UID-first knowledge architecture, and safe Obsidian workspace tooling.

VGTREE has no telemetry and requires no hosted service. The core engine makes no network calls.

## Why VGTREE

- Simple T0/T1 work stays direct; complex T2-T4 work receives governed Tree execution.
- Risk signals can raise classification but cannot be overridden by a lower caller-selected class.
- Branch dependencies form a validated DAG with primary, secondary, and deferred scope.
- Phase transitions, branch status, and completion gates are computed from state and evidence.
- Atomic state writes and explicit locks protect resumable local work.
- Core and Governed UID modes connect project structure to Obsidian discoverability.
- A skills-only plugin provides six composable Agent Skills without MCP, hooks, apps, or authentication.

## Install

Python 3.10 or newer is required.

```bash
pip install git+https://github.com/scandium1102/vgtree.git@v1.0.0
vgtree --help
```

For development:

```bash
git clone https://github.com/scandium1102/vgtree.git
cd vgtree
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Quick start

Start from [examples/task.json](examples/task.json):

```bash
vgtree classify --task examples/task.json
vgtree init --task examples/task.json --state .vgtree/tasks/example.json
vgtree next --state .vgtree/tasks/example.json
vgtree validate --state .vgtree/tasks/example.json
```

During branch execution:

```bash
vgtree guard --state .vgtree/tasks/example.json --branch build --activity "run bounded implementation batch"
vgtree set-branch --state .vgtree/tasks/example.json --branch build --status IN_PROGRESS
vgtree record-evidence --state .vgtree/tasks/example.json --branch build --evidence examples/evidence.json
vgtree set-branch --state .vgtree/tasks/example.json --branch build --status VERIFIED
```

The JSON result status maps to process exits: `PASS=0`, `FAIL=1`, `REVIEW_REQUIRED=2`, and `BLOCKED=3`.

## Obsidian

Audit an existing vault without changing it:

```bash
vgtree obsidian audit --vault /path/to/vault --mode core
vgtree obsidian plan --vault /path/to/vault --mode governed --output /outside/vault/plan.json
```

Create a new starter only in a new or empty destination:

```bash
vgtree obsidian scaffold --destination /path/to/new-vault --mode core
```

VGTREE v1 does not apply, move, rename, rewrite, or delete files in an existing vault. See [the Obsidian guide](docs/obsidian.md).

## OpenAI plugin and six Skills

The skills-only plugin includes:

- `using-vgtree`
- `planning-tree-work`
- `executing-tree-work`
- `verifying-tree-work`
- `governing-knowledge-architecture`
- `building-obsidian-workspaces`

For a local Codex installation, clone the repository, add its root as a local marketplace, then install `vgtree@vgtree`. Exact instructions are in [docs/plugin.md](docs/plugin.md). The skills follow the open Agent Skills format and keep engine logic in the tested CLI/API.

## Python API

```python
from vgtree import VGTREEEngine

engine = VGTREEEngine()
result = engine.initialize(task)
if result.status == "PASS":
    state = result.data["state"]
```

## Documentation

- [Architecture](docs/architecture.md)
- [UID modes](docs/uid-modes.md)
- [Obsidian](docs/obsidian.md)
- [Schema 1.1 migration](docs/migration.md)
- [Plugin and Skills](docs/plugin.md)
- [Traditional Chinese quick start](README.zh-TW.md)

## Boundaries

VGTREE is a control plane, not a replacement for domain tests, security scanners, database rollback tools, remote authorization, or authoritative readback. A structurally valid evidence record must still be produced honestly by the relevant tool.

MCP, hosted execution, telemetry, automatic mutation of existing vaults, and a custom Obsidian plugin are intentionally outside v1.0.

## License and policies

MIT licensed. See [Security](SECURITY.md), [Privacy](PRIVACY.md), [Terms](TERMS.md), [Support](SUPPORT.md), and [Contributing](CONTRIBUTING.md).
