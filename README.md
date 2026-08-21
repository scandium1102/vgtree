<p align="center">
  <img src="plugins/vgtree/assets/logo.svg" alt="VGTREE" width="520">
</p>

# VGTREE

Branch complex work into verifiable outcomes.

**Map the whole outcome. Cover every required branch. Go deep only after the wide pass. Bind completion evidence to inspectable receipts.**

VGTREE is a local-first workflow system for ChatGPT, Codex, other agents, and Obsidian. Six portable Skills work immediately from the plugin directory; the optional Python Engine adds deterministic schemas, state transitions, coverage gates, receipt binding, and JSON CLI results.

VGTREE is MIT licensed and free. It has no account, hosted service, MCP server, telemetry, analytics, or automatic mutation of an existing Obsidian vault.

## Two modes

- **ENGINE** — a compatible VGTREE 1.1 CLI computes gates and may return machine-verified `PASS`.
- **SKILL_ONLY** — packaged templates, schemas, and references support planning and review without installing software. It reports `engine_validation=NOT_RUN`; overall status cannot exceed `REVIEW_REQUIRED`.

Skills never install the Engine automatically.

## Install

Python 3.10 or newer is required for the Engine:

```bash
pip install vgtree==1.1.0
vgtree --version
```

Until the PyPI release is live, install the exact GitHub tag:

```bash
pip install git+https://github.com/scandium1102/vgtree.git@v1.1.0
vgtree --help
```

The Skills-only plugin can be installed from the OpenAI universal Plugins Directory after approval, or inspected locally under [plugins/vgtree](plugins/vgtree).

## Map → Cover → Deepen → Prove

### 1. Map

Describe the complete outcome with a Capability Map, shared interfaces, high-risk `PRE_EXECUTION` owners, minimum viable states, and final acceptance:

```bash
vgtree map validate --map examples/capability-map.json
vgtree map compile --map examples/capability-map.json --output task.json
vgtree classify --task task.json
vgtree init --task task.json --state state.json
```

### 2. Coverage Gate: Cover

State 2.1 requires exact baseline evidence for every `coverage_required` branch. Baseline evidence proves wide-pass presence, not completion.

```bash
vgtree record-evidence --state state.json --branch authorize --evidence examples/baseline-evidence.json
vgtree coverage --state state.json
```

### 3. Deepen

A `REQUIRED` policy blocks deep work until coverage passes. An `ADVISORY` override needs a recorded reason.

```bash
vgtree advance-depth --state state.json
vgtree guard --state state.json --branch deploy --activity "bounded implementation" --depth deep
```

### 4. Prove

Detailed Tool Receipts stay as local sidecars. Compact evidence binds the exact receipt bytes into state without copying tool detail into the ledger.

```bash
vgtree receipt validate --root examples --receipt examples/receipt.json
vgtree receipt evidence --root examples --receipt examples/receipt.json --output receipt-evidence.json
vgtree record-evidence --state state.json --branch deploy --evidence receipt-evidence.json
```

Branch success remains separate from integration and final verification:

```bash
vgtree record-evidence --state state.json --evidence integration.json
vgtree next --state state.json
vgtree record-evidence --state state.json --evidence final-verification.json
vgtree complete --state state.json
```

Exit codes map to `PASS=0`, `FAIL=1`, `REVIEW_REQUIRED=2`, and `BLOCKED=3`.

## Six Skills

- `using-vgtree`
- `planning-tree-work`
- `executing-tree-work`
- `verifying-tree-work`
- `governing-knowledge-architecture`
- `building-obsidian-workspaces`

The default Context Budget is one primary Skill bundle plus at most one support bundle. Extra bundles need a name, reason, and unload condition.

## Obsidian as a first-class integration

VGTREE combines Tree execution with UID-first knowledge architecture:

- **Core**: project UID, canonical owner/root, registry, Home, Map, Status, Todo, and rollback for risky work.
- **Governed**: Core plus file UID, raw-byte SHA-256, provenance, lineage, journaled transactions, reference coverage, readback, and rollback evidence.

Audit or plan an existing vault without changing its notes:

```bash
vgtree obsidian audit --vault /path/to/vault --mode core
vgtree obsidian plan --vault /path/to/vault --mode governed --output /outside/vault/plan.json
```

Create a starter only in a new or empty destination:

```bash
vgtree obsidian scaffold --destination /path/to/new-vault --mode core
```

VGTREE 1.1 does not apply, move, rename, rewrite, or delete files in an existing vault.

## Trust boundaries

- A valid Capability Map proves contract consistency, not that its planning assumptions are true.
- Baseline evidence cannot replace Definition of Done, integration, or final-verification evidence.
- Receipt validation is structural and exact-byte-bound; the producing tool remains responsible for truth.
- The Engine is out-of-process local software. Protect state, receipt, and vault directories with private filesystem permissions.
- External publication, destructive work, payments, accounts, and identity verification remain host/user authorization decisions.
- Behavioral examples are shape-only unless a result discloses provider, model, reasoning setting, tools, date, trials, fixture digest, and artifacts.

## Documentation

- [Architecture](docs/architecture.md)
- [Plugin and Skills](docs/plugin.md)
- [Obsidian](docs/obsidian.md)
- [UID modes](docs/uid-modes.md)
- [Migration](docs/migration.md)
- [Traditional Chinese](README.zh-TW.md)
- [Security](SECURITY.md)
- [Privacy](PRIVACY.md)
- [Terms](TERMS.md)
- [Support](SUPPORT.md)

## Development

```bash
git clone https://github.com/scandium1102/vgtree.git
cd vgtree
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/validate_v1_1_evals.py
```

VGTREE uses the MIT License.
