from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillOnlyEnvironmentTests(unittest.TestCase):
    def test_clean_environment_selects_honest_skill_only_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            empty_path = Path(raw) / "empty-path"
            empty_path.mkdir()
            env = os.environ.copy()
            env["PATH"] = str(empty_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_skill_only.py"),
                    "--plugin-root",
                    str(ROOT / "plugins" / "vgtree"),
                    "--require-engine-absent",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("PASS", result["validation_status"])
        self.assertEqual("SKILL_ONLY", result["runtime_mode"])
        self.assertEqual("NOT_RUN", result["engine_validation"])
        self.assertEqual("REVIEW_REQUIRED", result["overall_status"])
        self.assertFalse(result["engine_present"])
        self.assertFalse(result["installed_software"])
        self.assertEqual(6, result["skills"])


if __name__ == "__main__":
    unittest.main()
