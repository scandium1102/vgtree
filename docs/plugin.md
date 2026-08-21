# OpenAI Plugin and Agent Skills

The VGTREE plugin is skills-only. It contains no MCP server, app, hook, authentication flow, connector, hosted account, or telemetry.

## Contents

The six Skills cover routing, planning, execution, verification, knowledge architecture, and Obsidian workspace operations. Shared Skill-only schemas, templates, and references live under `plugins/vgtree/shared/`; they preserve one contract and do not duplicate the Python Engine. Evaluation records live under `evals/`.

## Runtime modes

- `ENGINE`: `vgtree --version` reports a compatible 1.1.x CLI. Commands may return deterministic `PASS` from validated machine evidence.
- `SKILL_ONLY`: the CLI is absent or incompatible. Skills do not install it. They use the packaged resources, report `engine_validation=NOT_RUN`, and cap overall status at `REVIEW_REQUIRED`.

The OpenAI universal Plugins Directory bundle is useful immediately in SKILL_ONLY mode. PyPI and GitHub provide the optional Engine.

## Local Codex installation

Clone the repository. The Skills work without the Python CLI; install the Engine only when deterministic gates are wanted:

```bash
git clone https://github.com/scandium1102/vgtree.git
cd vgtree
python -m pip install -e .  # optional Engine
```

Add the clone root as a local marketplace and install the plugin using the marketplace name in `.agents/plugins/marketplace.json`:

```bash
codex plugin marketplace add /absolute/path/to/vgtree
codex plugin add vgtree@vgtree
```

Start a new Codex task after installation so the Skills are discovered in a fresh context.

## Validation

```bash
python C:/path/to/plugin-creator/scripts/validate_plugin.py plugins/vgtree
python -m unittest discover -s tests -p "test_plugin.py" -v
python -m unittest discover -s tests -p "test_skills.py" -v
```

The repository marketplace is intended for local and source installations. OpenAI Plugin Directory distribution uses the reviewed release repository and current OpenAI submission flow.

## Safety

Skills can change agent behavior. Review the installed source and release tag. Templates and prose never become successful machine execution; only a compatible Engine can produce deterministic gate results.
