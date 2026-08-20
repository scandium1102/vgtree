from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_engine import evidence, initialized_state
from test_persistence import legacy_state
from test_validation import valid_task


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "vgtree", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


class CoreCliTests(unittest.TestCase):
    def test_classify_emits_pass_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_path = Path(directory) / "task.json"
            task = valid_task()
            task["explicit_class"] = "T0"
            task["signals"]["migration"] = True
            task_path.write_text(json.dumps(task), encoding="utf-8")

            completed = run_cli("classify", "--task", str(task_path))
            payload = json.loads(completed.stdout)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["data"]["decision"]["task_class"], "T3")

    def test_init_writes_state_and_blocks_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_path = Path(directory) / "task.json"
            state_path = Path(directory) / "state.json"
            task_path.write_text(json.dumps(valid_task()), encoding="utf-8")

            first = run_cli(
                "init", "--task", str(task_path), "--state", str(state_path)
            )
            second = run_cli(
                "init", "--task", str(task_path), "--state", str(state_path)
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue(state_path.is_file())
            self.assertEqual(second.returncode, 3)
            self.assertEqual(json.loads(second.stdout)["status"], "BLOCKED")

    def test_next_returns_review_required_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = initialized_state()
            state["phase"] = "branch_execution"
            state["branches"][0]["status"] = "IN_PROGRESS"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            completed = run_cli("next", "--state", str(state_path))
            payload = json.loads(completed.stdout)

            self.assertEqual(completed.returncode, 2)
            self.assertEqual(payload["status"], "REVIEW_REQUIRED")
            self.assertEqual(payload["code"], "BRANCHES_INCOMPLETE")

    def test_guard_returns_blocked_exit_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state_path.write_text(json.dumps(initialized_state()), encoding="utf-8")

            completed = run_cli(
                "guard",
                "--state",
                str(state_path),
                "--branch",
                "docs",
                "--activity",
                "write guide",
            )

            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["code"], "DEPENDENCY_UNSATISFIED")

    def test_validate_and_complete_use_json_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = initialized_state()
            state["phase"] = "verification"
            state["branches"][0]["status"] = "VERIFIED"
            state["evidence"] = [
                evidence("ev-integration", "integration"),
                evidence("ev-final", "final-verification"),
            ]
            state_path.write_text(json.dumps(state), encoding="utf-8")

            validated = run_cli("validate", "--state", str(state_path))
            completed = run_cli("complete", "--state", str(state_path))

            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(json.loads(validated.stdout)["status"], "PASS")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["code"], "COMPLETE")
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["phase"], "complete"
            )

    def test_migrate_state_writes_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "old.json"
            output = Path(directory) / "new.json"
            source.write_text(json.dumps(legacy_state()), encoding="utf-8")

            completed = run_cli(
                "migrate-state", "--input", str(source), "--output", str(output)
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "PASS")
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["schema_version"], "2.0"
            )

    def test_missing_file_and_usage_error_never_emit_traceback(self) -> None:
        missing = run_cli("classify", "--task", "does-not-exist.json")
        usage = run_cli("guard")

        for completed in (missing, usage):
            with self.subTest(arguments=completed.args):
                self.assertEqual(completed.returncode, 1)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "FAIL")
                self.assertNotIn("Traceback", completed.stderr + completed.stdout)


if __name__ == "__main__":
    unittest.main()
