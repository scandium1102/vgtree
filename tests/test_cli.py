from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_capability import valid_map
from test_coverage import covered_state, coverage_task
from test_engine import at_phase, evidence, initialized_state
from test_persistence import legacy_state
from test_receipts import valid_receipt
from test_validation import valid_task
from vgtree.engine import VGTREEEngine
from vgtree.validation import validate_evidence, validate_task


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "vgtree", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


class CoreCliTests(unittest.TestCase):
    def test_receipt_validate_and_evidence_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "receipts"
            root.mkdir()
            receipt = root / "receipt.json"
            output = Path(directory) / "evidence.json"
            receipt.write_text(json.dumps(valid_receipt()), encoding="utf-8")

            validated = run_cli(
                "receipt", "validate", "--root", str(root), "--receipt", str(receipt)
            )
            created = run_cli(
                "receipt",
                "evidence",
                "--root",
                str(root),
                "--receipt",
                str(receipt),
                "--output",
                str(output),
            )

            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertTrue(validate_evidence(json.loads(output.read_text(encoding="utf-8"))).valid)

    def test_receipt_evidence_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "receipts"
            root.mkdir()
            receipt = root / "receipt.json"
            output = Path(directory) / "evidence.json"
            receipt.write_text(json.dumps(valid_receipt()), encoding="utf-8")
            output.write_text("owner bytes", encoding="utf-8")
            result = run_cli(
                "receipt",
                "evidence",
                "--root",
                str(root),
                "--receipt",
                str(receipt),
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 3)
            self.assertEqual(output.read_text(encoding="utf-8"), "owner bytes")

    def test_receipt_attachment_keeps_only_compact_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipts = root / "receipts"
            receipts.mkdir()
            receipt = receipts / "receipt.json"
            evidence_path = root / "evidence.json"
            state_path = root / "state.json"
            receipt.write_text(json.dumps(valid_receipt()), encoding="utf-8")
            state_path.write_text(json.dumps(initialized_state()), encoding="utf-8")

            created = run_cli(
                "receipt",
                "evidence",
                "--root",
                str(receipts),
                "--receipt",
                str(receipt),
                "--output",
                str(evidence_path),
            )
            attached = run_cli(
                "record-evidence",
                "--state",
                str(state_path),
                "--evidence",
                str(evidence_path),
                "--branch",
                "build",
            )
            saved = json.loads(state_path.read_text(encoding="utf-8"))

            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(attached.returncode, 0, attached.stderr)
            compact = saved["branches"][0]["evidence"][0]
            self.assertIn("digest", compact)
            self.assertIn("reference", compact)
            self.assertNotIn("tool", compact)
            self.assertNotIn("validations", compact)

    def test_coverage_and_advance_depth_persist_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = covered_state()
            state_path.write_text(json.dumps(state), encoding="utf-8")

            report = run_cli("coverage", "--state", str(state_path))
            advanced = run_cli("advance-depth", "--state", str(state_path))
            saved = json.loads(state_path.read_text(encoding="utf-8"))

            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            self.assertEqual(saved["coverage"]["execution_stage"], "DEEP")

    def test_advance_depth_lock_collision_preserves_state_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state_path.write_text(json.dumps(covered_state()), encoding="utf-8")
            before = state_path.read_bytes()
            state_path.with_name("state.json.lock").write_text(
                "other writer", encoding="utf-8"
            )

            result = run_cli("advance-depth", "--state", str(state_path))

            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads(result.stdout)["code"], "STATE_LOCKED")
            self.assertEqual(state_path.read_bytes(), before)

    def test_guard_depth_is_forwarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = VGTREEEngine().initialize(coverage_task()).data["state"]
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = run_cli(
                "guard",
                "--state",
                str(state_path),
                "--branch",
                "authorize",
                "--activity",
                "deep optimization",
                "--depth",
                "deep",
            )
            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads(result.stdout)["code"], "DEEP_STAGE_NOT_ACTIVE")

    def test_map_validate_and_compile_never_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "map.json"
            output = root / "task.json"
            source.write_text(json.dumps(valid_map()), encoding="utf-8")

            validated = run_cli("map", "validate", "--map", str(source))
            first = run_cli(
                "map", "compile", "--map", str(source), "--output", str(output)
            )
            second = run_cli(
                "map", "compile", "--map", str(source), "--output", str(output)
            )

            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 3)
            self.assertEqual(json.loads(second.stdout)["code"], "TASK_OUTPUT_EXISTS")
            self.assertTrue(validate_task(json.loads(output.read_text(encoding="utf-8"))).valid)

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

    def test_classify_uses_explicit_workflow_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task_path = Path(directory) / "task.json"
            registry_path = Path(directory) / "workflows.json"
            task = valid_task()
            task["specialized_match"] = {
                "workflow_ref": "WF-SPECIAL@1.0",
                "registered": True,
                "trigger_match": True,
                "context_match": True,
                "capability_match": True,
                "outcome_match": True,
                "safety_match": True,
            }
            task_path.write_text(json.dumps(task), encoding="utf-8")
            registry_path.write_text(
                json.dumps(
                    {
                        "workflows": [
                            {"workflow_ref": "WF-SPECIAL@1.0", "status": "ACTIVE"}
                        ]
                    }
                ),
                encoding="utf-8",
            )

            without_registry = run_cli("classify", "--task", str(task_path))
            with_registry = run_cli(
                "classify",
                "--task",
                str(task_path),
                "--registry",
                str(registry_path),
            )

            self.assertEqual(
                json.loads(without_registry.stdout)["data"]["decision"]["route"], "tree"
            )
            self.assertEqual(
                json.loads(with_registry.stdout)["data"]["decision"]["route"],
                "specialized",
            )

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
            at_phase(state, "branch_execution")
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
            at_phase(state, "verification")
            state["branches"][0]["status"] = "VERIFIED"
            state["branches"][0]["evidence"] = [evidence("ev-build", "test")]
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

    def test_record_evidence_and_set_branch_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            evidence_path = Path(directory) / "evidence.json"
            state_path.write_text(json.dumps(initialized_state()), encoding="utf-8")
            evidence_path.write_text(
                json.dumps(evidence("ev-build", "test")), encoding="utf-8"
            )

            started = run_cli(
                "set-branch",
                "--state",
                str(state_path),
                "--branch",
                "build",
                "--status",
                "IN_PROGRESS",
            )
            recorded = run_cli(
                "record-evidence",
                "--state",
                str(state_path),
                "--branch",
                "build",
                "--evidence",
                str(evidence_path),
            )
            verified = run_cli(
                "set-branch",
                "--state",
                str(state_path),
                "--branch",
                "build",
                "--status",
                "VERIFIED",
            )

            self.assertEqual(started.returncode, 0, started.stderr)
            self.assertEqual(recorded.returncode, 0, recorded.stderr)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["branches"][0]["status"], "VERIFIED")


class ObsidianCliTests(unittest.TestCase):
    def test_scaffold_and_audit_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"

            scaffold = run_cli(
                "obsidian", "scaffold", "--destination", str(vault), "--mode", "core"
            )
            audit = run_cli(
                "obsidian", "audit", "--vault", str(vault), "--mode", "core"
            )

            self.assertEqual(scaffold.returncode, 0, scaffold.stderr)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertEqual(json.loads(audit.stdout)["code"], "OBSIDIAN_AUDIT_PASS")

    def test_plan_writes_only_to_new_path_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            vault.mkdir()
            output = Path(directory) / "plan.json"
            before = list(vault.rglob("*"))

            completed = run_cli(
                "obsidian",
                "plan",
                "--vault",
                str(vault),
                "--mode",
                "governed",
                "--output",
                str(output),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output.is_file())
            self.assertEqual(list(vault.rglob("*")), before)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["status"], "PASS")

    def test_plan_rejects_output_inside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            vault.mkdir()
            output = vault / "plan.json"

            completed = run_cli(
                "obsidian",
                "plan",
                "--vault",
                str(vault),
                "--mode",
                "core",
                "--output",
                str(output),
            )

            self.assertEqual(completed.returncode, 3)
            self.assertFalse(output.exists())
            self.assertEqual(
                json.loads(completed.stdout)["code"], "OBSIDIAN_PLAN_OUTPUT_UNSAFE"
            )


if __name__ == "__main__":
    unittest.main()
