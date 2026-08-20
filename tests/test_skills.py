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


if __name__ == "__main__":
    unittest.main()
