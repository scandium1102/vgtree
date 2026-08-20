from __future__ import annotations

import unittest
import json
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "plugins" / "vgtree" / "skills"
SHARED_ROOT = REPOSITORY_ROOT / "plugins" / "vgtree" / "shared"


def load_skill(name: str) -> tuple[dict, str]:
    path = SKILLS_ROOT / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"{name} is missing frontmatter")
    closing = lines.index("---", 1)
    metadata = yaml.safe_load("\n".join(lines[1:closing]))
    return metadata, "\n".join(lines[closing + 1 :])


class UsingVgtreeSkillTests(unittest.TestCase):
    def test_using_vgtree_has_valid_identity_and_machine_steps(self) -> None:
        metadata, body = load_skill("using-vgtree")

        self.assertEqual(metadata["name"], "using-vgtree")
        self.assertIn("complex", metadata["description"].lower())
        self.assertIn("vgtree classify", body)
        self.assertIn("vgtree init", body)
        self.assertIn("vgtree validate", body)
        self.assertIn("Never", body)
        self.assertIn("untrusted data", body)
        self.assertIn("argument array", body)
        self.assertIn("vgtree --version", body)
        self.assertIn("runtime_mode", body)
        self.assertIn("engine_validation", body)
        self.assertIn("SKILL_ONLY", body)
        self.assertIn("one primary", body)
        self.assertIn("one support", body)
        self.assertIn("unload condition", body.lower())

    def test_skill_only_contract_never_installs_or_claims_pass(self) -> None:
        for path in SKILLS_ROOT.glob("*/SKILL.md"):
            body = path.read_text(encoding="utf-8")
            with self.subTest(skill=path.parent.name):
                self.assertIn("SKILL_ONLY", body)
                self.assertIn("engine_validation=NOT_RUN", body)
                self.assertIn("REVIEW_REQUIRED", body)
                self.assertIn("Do not install", body)

    def test_shared_skill_only_resources_are_present_and_canonical(self) -> None:
        for name in (
            "capability-map.schema.json",
            "task.schema.json",
            "state.schema.json",
            "receipt.schema.json",
        ):
            self.assertEqual(
                json.loads((SHARED_ROOT / "schemas" / name).read_text(encoding="utf-8")),
                json.loads(
                    (REPOSITORY_ROOT / "schemas" / name).read_text(encoding="utf-8")
                ),
                name,
            )
        for relative in (
            "references/runtime-modes.md",
            "references/obsidian-audit-checklist.md",
            "templates/capability-map.json",
            "templates/skill-only-work-record.json",
            "templates/receipt.json",
        ):
            self.assertTrue((SHARED_ROOT / relative).is_file(), relative)

    def test_v11_skill_scenarios_disclose_modes_and_forbidden_behavior(self) -> None:
        scenarios = (
            "planning-tree-work/scenario-002-capability-map.md",
            "executing-tree-work/scenario-002-coverage-depth.md",
            "verifying-tree-work/scenario-002-receipt-binding.md",
            "using-vgtree/scenario-002-context-budget.md",
        )
        for relative in scenarios:
            text = (REPOSITORY_ROOT / "evals" / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("Baseline without v1.1 passage", text)
                self.assertIn("Expected with the Skill", text)
                self.assertIn("Commands and results", text)
                self.assertIn("Forbidden behavior", text)
                self.assertIn("Evidence artifact", text)
                self.assertIn("Context Budget", text)


class PlanningTreeWorkSkillTests(unittest.TestCase):
    def test_planning_skill_requires_dag_and_breadth(self) -> None:
        metadata, body = load_skill("planning-tree-work")

        self.assertEqual(metadata["name"], "planning-tree-work")
        self.assertIn("plan", metadata["description"].lower())
        self.assertIn("Definition of Done", body)
        self.assertIn("depends_on", body)
        self.assertIn("DEFERRED", body)
        self.assertIn("vgtree classify", body)
        self.assertIn("vgtree map validate", body)
        self.assertIn("vgtree map compile", body)
        self.assertIn("minimum_viable_state", body)
        self.assertIn("shared_interfaces", body)
        self.assertIn("PRE_EXECUTION", body)


class ExecutingTreeWorkSkillTests(unittest.TestCase):
    def test_execution_skill_uses_guards_and_legal_mutations(self) -> None:
        metadata, body = load_skill("executing-tree-work")

        self.assertEqual(metadata["name"], "executing-tree-work")
        self.assertIn("execute", metadata["description"].lower())
        self.assertIn("vgtree guard", body)
        self.assertIn("vgtree set-branch", body)
        self.assertIn("vgtree record-evidence", body)
        self.assertIn("rabbit hole", body.lower())
        self.assertIn("BLOCKED", body)
        self.assertIn("untrusted data", body)
        self.assertIn("argument array", body)
        self.assertIn("vgtree coverage", body)
        self.assertIn("vgtree advance-depth", body)
        self.assertIn("--depth", body)
        self.assertIn("branch:<branch-id>:baseline", body)
        self.assertIn("Baseline evidence is not completion evidence", body)


class VerifyingTreeWorkSkillTests(unittest.TestCase):
    def test_verification_skill_requires_fresh_integration_and_readback(self) -> None:
        metadata, body = load_skill("verifying-tree-work")

        self.assertEqual(metadata["name"], "verifying-tree-work")
        self.assertIn("verify", metadata["description"].lower())
        self.assertIn("integration", body)
        self.assertIn("final-verification", body)
        self.assertIn("vgtree complete", body)
        self.assertIn("readback", body.lower())
        self.assertIn("owner", body.lower())
        self.assertIn("vgtree receipt validate", body)
        self.assertIn("vgtree receipt evidence", body)
        self.assertIn("exact receipt bytes", body)


class GoverningKnowledgeArchitectureSkillTests(unittest.TestCase):
    def test_governance_skill_defines_uid_authority_and_modes(self) -> None:
        metadata, body = load_skill("governing-knowledge-architecture")

        self.assertEqual(metadata["name"], "governing-knowledge-architecture")
        self.assertIn("knowledge", metadata["description"].lower())
        self.assertIn("Core mode", body)
        self.assertIn("Governed mode", body)
        self.assertIn("project UID", body)
        self.assertIn("file UID", body)
        self.assertIn("Home", body)
        self.assertIn("transaction", body.lower())
        self.assertIn("vgtree obsidian audit", body)


class BuildingObsidianWorkspacesSkillTests(unittest.TestCase):
    def test_obsidian_skill_separates_existing_and_new_vaults(self) -> None:
        metadata, body = load_skill("building-obsidian-workspaces")

        self.assertEqual(metadata["name"], "building-obsidian-workspaces")
        self.assertIn("obsidian", metadata["description"].lower())
        self.assertIn("existing vault", body.lower())
        self.assertIn("new or empty", body.lower())
        self.assertIn("vgtree obsidian audit", body)
        self.assertIn("vgtree obsidian plan", body)
        self.assertIn("vgtree obsidian scaffold", body)
        self.assertIn("--live", body)
        self.assertIn("does not apply", body.lower())


if __name__ == "__main__":
    unittest.main()
