from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vgtree.migration import migrate_state, migrate_state_file
from vgtree.store import StateStore

from test_engine import initialized_state


def legacy_state() -> dict:
    return {
        "schema_version": "1.1",
        "workflow_ref": "WF-VEGA-TREE@1.0",
        "task_class": "T3",
        "phase": "breadth_pass",
        "mission": {
            "objective": "Migrate a governed workflow",
            "primary_deliverables": ["Working migration"],
            "secondary_deliverables": ["Guide"],
            "optional_improvements": [],
            "constraints": ["Preserve evidence"],
            "definition_of_done": ["New state validates"],
            "known_risks": ["Schema drift"],
        },
        "primary_branches": [
            {
                "id": "build",
                "label": "Build migration",
                "priority": "BLOCKING",
                "status": "verified",
                "dependencies": [],
                "evidence": ["legacy test passed"],
            },
            {
                "id": "blocked_branch",
                "label": "External review",
                "priority": "IMPORTANT",
                "status": "blocked",
                "dependencies": ["build"],
                "blocker": "External review is unavailable",
                "accepted_limitation": True,
                "evidence": ["review unavailable"],
            },
        ],
        "cross_cutting": [],
        "deferred": [{"item": "Optional dashboard", "reason": "Out of scope"}],
        "budgets": {
            "research": {
                "decision_target": "migration mapping",
                "stop_condition": "mapping complete",
                "no_decision_delta_batches": 0,
            },
            "context": {"loaded_layers": ["global_minimal"]},
        },
        "worktree_hygiene": {"applicability": "not_applicable", "repositories": []},
        "gates": {
            "skeleton_complete": True,
            "core_complete": True,
            "integration_passed": False,
            "worktree_hygiene_passed": True,
            "final_verification_passed": False,
        },
        "evidence": ["legacy state captured"],
    }


class StateStoreTests(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            store = StateStore()
            state = initialized_state()

            saved = store.save(path, state)
            loaded = store.load(path)

            self.assertEqual(saved.status, "PASS", saved)
            self.assertEqual(loaded.status, "PASS", loaded)
            self.assertEqual(loaded.data["state"], state)
            self.assertFalse(path.with_name("state.json.lock").exists())

    def test_lock_collision_is_blocked_and_preserves_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            original = '{"original": true}\n'
            path.write_text(original, encoding="utf-8")
            path.with_name("state.json.lock").write_text("other writer", encoding="utf-8")

            result = StateStore().save(path, initialized_state())

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.code, "STATE_LOCKED")
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertTrue(path.with_name("state.json.lock").exists())

    def test_invalid_state_is_not_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = initialized_state()
            state["phase"] = "invented"

            result = StateStore().save(path, state)

            self.assertEqual(result.status, "FAIL")
            self.assertEqual(result.code, "STATE_INVALID")
            self.assertFalse(path.exists())

    def test_malformed_json_load_is_controlled_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("{broken", encoding="utf-8")

            result = StateStore().load(path)

            self.assertEqual(result.status, "FAIL")
            self.assertEqual(result.code, "STATE_JSON_INVALID")


class MigrationTests(unittest.TestCase):
    def test_legacy_1_1_state_migrates_to_valid_2_0_state(self) -> None:
        result = migrate_state(legacy_state(), migrated_at="2026-08-20T00:00:00Z")

        self.assertEqual(result.status, "PASS", result)
        state = result.data["state"]
        self.assertEqual(state["schema_version"], "2.0")
        self.assertEqual(state["phase"], "branch_execution")
        self.assertEqual(state["branches"][0]["status"], "VERIFIED")
        self.assertEqual(state["branches"][1]["status"], "ACCEPTED_LIMITATION")
        self.assertEqual(state["branches"][2]["priority"], "DEFERRED")

    def test_unknown_schema_version_is_rejected(self) -> None:
        old = legacy_state()
        old["schema_version"] = "0.1"

        result = migrate_state(old)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.code, "MIGRATION_VERSION_UNSUPPORTED")

    def test_file_migration_never_overwrites_source_or_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "old.json"
            output = Path(directory) / "new.json"
            source.write_text(json.dumps(legacy_state()), encoding="utf-8")

            same_path = migrate_state_file(source, source)
            self.assertEqual(same_path.code, "MIGRATION_OVERWRITE_FORBIDDEN")

            output.write_text("keep me", encoding="utf-8")
            collision = migrate_state_file(source, output)
            self.assertEqual(collision.status, "BLOCKED")
            self.assertEqual(output.read_text(encoding="utf-8"), "keep me")


if __name__ == "__main__":
    unittest.main()
