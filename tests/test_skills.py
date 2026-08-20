from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "plugins" / "vgtree" / "skills"


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


class PlanningTreeWorkSkillTests(unittest.TestCase):
    def test_planning_skill_requires_dag_and_breadth(self) -> None:
        metadata, body = load_skill("planning-tree-work")

        self.assertEqual(metadata["name"], "planning-tree-work")
        self.assertIn("plan", metadata["description"].lower())
        self.assertIn("Definition of Done", body)
        self.assertIn("depends_on", body)
        self.assertIn("DEFERRED", body)
        self.assertIn("vgtree classify", body)


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


if __name__ == "__main__":
    unittest.main()
