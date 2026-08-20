import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class ReleaseWorkflowTests(unittest.TestCase):
    def test_pages_workflow_is_split_pinned_and_least_privilege(self) -> None:
        text = (WORKFLOWS / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [main]", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("group: pages", text)
        self.assertIn("contents: read", text)
        self.assertRegex(text, r"(?m)^  build:")
        self.assertRegex(text, r"(?m)^  deploy:")
        self.assertIn("needs: build", text)
        self.assertIn("name: github-pages", text)
        self.assertIn("pages: write", text)
        self.assertIn("id-token: write", text)
        self.assertIn("path: site", text)
        uses = re.findall(r"uses:\s*([^\s#]+)", text)
        self.assertEqual(4, len(uses))
        for action in uses:
            self.assertRegex(action, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")
        self.assertIn("actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d", text)
        self.assertIn("actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9", text)
        self.assertIn("actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128", text)


if __name__ == "__main__":
    unittest.main()
