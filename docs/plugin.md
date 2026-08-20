# OpenAI Plugin and Agent Skills

The VGTREE plugin is skills-only. It contains no MCP server, app, hook, authentication flow, or connector.

## Contents

The six Skills cover routing, planning, execution, verification, knowledge architecture, and Obsidian workspace operations. Each Skill was evaluated with a baseline scenario before authoring and the same scenario after loading the Skill. Evaluation records live under `evals/`.

## Local Codex installation

Clone the repository and install the Python CLI first:

```bash
git clone https://github.com/scandium1102/vgtree.git
cd vgtree
python -m pip install -e .
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

Skills can change agent behavior. Review the installed source and release tag. VGTREE Skills require the tested CLI/API for machine gates and do not treat prose as successful execution.
