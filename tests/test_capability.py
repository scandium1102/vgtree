from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from vgtree.capability import (
    compile_capability_map,
    load_capability_map,
    validate_capability_map,
)
from vgtree.validation import validate_task


def valid_map(policy: str = "REQUIRED") -> dict:
    return {
        "map_version": "1.0",
        "task_id": "release-example",
        "title": "Release an integrated product",
        "goal": "Verified release and authoritative readback",
        "signals": {
            "estimated_files": 20,
            "migration": False,
            "project_scale": True,
            "external_effect": True,
            "destructive": False,
            "cross_system": True,
            "irreversible": False,
        },
        "wide_pass_policy": policy,
        "modules": [
            {
                "id": "authorize",
                "title": "Authorize release",
                "purpose": "Own the external-effect gate",
                "kind": "primary",
                "priority": "P0",
                "coverage_required": True,
                "depends_on": [],
                "minimum_viable_state": ["Release owner and target are known"],
                "baseline_evidence_requirements": ["Fresh authorization record"],
                "definition_of_done": ["Release is explicitly authorized"],
                "acceptance_evidence": ["Authorization evidence"],
                "shared_interfaces": ["release-target"],
                "deferred_details": [],
                "stop_condition": "Stop on approval or named blocker",
            },
            {
                "id": "deploy",
                "title": "Deploy release",
                "purpose": "Publish the integrated artifact",
                "kind": "primary",
                "priority": "P0",
                "coverage_required": True,
                "depends_on": ["authorize"],
                "minimum_viable_state": ["Target and rollback route are known"],
                "baseline_evidence_requirements": ["Fresh target inspection"],
                "definition_of_done": ["Approved artifact is available"],
                "acceptance_evidence": ["Deployment and readback evidence"],
                "shared_interfaces": ["release-target"],
                "deferred_details": ["Performance tuning"],
                "stop_condition": "Stop after readback or named blocker",
            },
        ],
        "cross_cutting_constraints": [
            {
                "id": "release-auth",
                "description": "External release requires approval",
                "owner_branch_id": "authorize",
                "module_ids": ["deploy"],
                "gate": "PRE_EXECUTION",
            }
        ],
        "final_acceptance_matrix": [
            {
                "id": "release-readback",
                "criterion": "Approved artifact is publicly readable",
                "module_ids": ["deploy"],
                "evidence_requirements": ["Authoritative readback"],
                "gate": "final-verification",
            }
        ],
    }


class CapabilityValidationTests(unittest.TestCase):
    def test_valid_map_passes(self) -> None:
        report = validate_capability_map(valid_map())
        self.assertTrue(report.valid, report.issues)

    def test_unknown_property_is_rejected(self) -> None:
        value = valid_map()
        value["trust_me"] = True
        self.assertFalse(validate_capability_map(value).valid)

    def test_duplicate_module_id_is_rejected(self) -> None:
        value = valid_map()
        value["modules"].append(copy.deepcopy(value["modules"][0]))
        self.assertIn(
            "CAPABILITY_ID_DUPLICATE",
            {item.code for item in validate_capability_map(value).issues},
        )

    def test_pre_execution_owner_must_be_real_dependency(self) -> None:
        value = valid_map()
        value["modules"][1]["depends_on"] = []
        self.assertIn(
            "CONSTRAINT_ORDER_UNENFORCED",
            {item.code for item in validate_capability_map(value).issues},
        )

    def test_acceptance_row_rejects_unknown_module(self) -> None:
        value = valid_map()
        value["final_acceptance_matrix"][0]["module_ids"] = ["missing"]
        self.assertIn(
            "ACCEPTANCE_MODULE_UNKNOWN",
            {item.code for item in validate_capability_map(value).issues},
        )

    def test_dependency_cycle_is_rejected(self) -> None:
        value = valid_map()
        value["modules"][0]["depends_on"] = ["deploy"]
        self.assertIn(
            "CAPABILITY_DEPENDENCY_CYCLE",
            {item.code for item in validate_capability_map(value).issues},
        )


class CapabilityCompilerTests(unittest.TestCase):
    def test_compile_preserves_execution_contract(self) -> None:
        digest = "sha256:" + ("1" * 64)
        result = compile_capability_map(valid_map(), source_digest=digest)
        self.assertEqual(result.status, "PASS", result)
        task = result.data["task"]
        self.assertEqual(task["task_id"], "release-example")
        self.assertEqual(
            task["branches"][1]["evidence_requirements"],
            ["Deployment and readback evidence"],
        )
        self.assertEqual(
            task["branches"][1]["minimum_viable_state"],
            ["Target and rollback route are known"],
        )
        self.assertEqual(task["capability_map"]["source_digest"], digest)
        self.assertTrue(validate_task(task).valid)

    def test_compile_rejects_invalid_source_digest(self) -> None:
        result = compile_capability_map(valid_map(), source_digest="sha256:short")
        self.assertEqual(result.code, "CAPABILITY_SOURCE_DIGEST_INVALID")

    def test_off_policy_compiles_to_original_task_shape(self) -> None:
        result = compile_capability_map(
            valid_map("OFF"), source_digest="sha256:" + ("2" * 64)
        )
        task = result.data["task"]
        self.assertNotIn("capability_map", task)
        self.assertNotIn("coverage_required", task["branches"][0])
        self.assertTrue(validate_task(task).valid)


class CapabilityFileTests(unittest.TestCase):
    def test_loader_hashes_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.json"
            raw = json.dumps(valid_map(), ensure_ascii=False).encode("utf-8")
            path.write_bytes(raw)
            loaded = load_capability_map(path)
            self.assertIsInstance(loaded, tuple)
            value, digest = loaded
            self.assertEqual(value["task_id"], "release-example")
            self.assertEqual(digest, "sha256:" + hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
