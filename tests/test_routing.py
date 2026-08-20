from __future__ import annotations

import copy
import unittest

from vgtree.routing import classify_task

from test_validation import valid_task


class ClassificationTests(unittest.TestCase):
    def test_explicit_class_can_upgrade_computed_class(self) -> None:
        task = valid_task()
        task["signals"]["estimated_files"] = 1
        task["explicit_class"] = "T3"

        decision = classify_task(task)

        self.assertEqual(decision.task_class, "T3")
        self.assertEqual(decision.route, "tree")

    def test_explicit_t0_cannot_downgrade_migration(self) -> None:
        task = valid_task()
        task["explicit_class"] = "T0"
        task["signals"]["estimated_files"] = 1
        task["signals"]["migration"] = True

        decision = classify_task(task)

        self.assertEqual(decision.task_class, "T3")
        self.assertEqual(decision.route, "tree")

    def test_explicit_t0_cannot_downgrade_project_scale(self) -> None:
        task = valid_task()
        task["explicit_class"] = "T0"
        task["signals"]["project_scale"] = True

        self.assertEqual(classify_task(task).task_class, "T3")

    def test_destructive_or_irreversible_task_is_t4(self) -> None:
        for signal in ("destructive", "irreversible"):
            with self.subTest(signal=signal):
                task = valid_task()
                task["explicit_class"] = "T0"
                task["signals"][signal] = True

                self.assertEqual(classify_task(task).task_class, "T4")

    def test_small_low_risk_task_stays_direct(self) -> None:
        task = valid_task()
        task["explicit_class"] = "T0"
        task["signals"]["estimated_files"] = 1

        decision = classify_task(task)

        self.assertEqual(decision.task_class, "T0")
        self.assertEqual(decision.route, "direct")


class SpecializedRoutingTests(unittest.TestCase):
    def match(self) -> dict:
        return {
            "workflow_ref": "WF-SPECIAL@1.0",
            "registered": True,
            "trigger_match": True,
            "context_match": True,
            "capability_match": True,
            "outcome_match": True,
            "safety_match": True,
        }

    def test_full_registered_match_routes_specialized(self) -> None:
        task = valid_task()
        task["specialized_match"] = self.match()

        decision = classify_task(task, registered_workflows={"WF-SPECIAL@1.0"})

        self.assertEqual(decision.route, "specialized")
        self.assertEqual(decision.workflow_ref, "WF-SPECIAL@1.0")

    def test_caller_registered_claim_does_not_register_workflow(self) -> None:
        task = valid_task()
        task["specialized_match"] = self.match()

        decision = classify_task(task, registered_workflows=set())

        self.assertEqual(decision.route, "tree")
        self.assertIsNone(decision.workflow_ref)

    def test_partial_match_routes_tree(self) -> None:
        for key in (
            "registered",
            "trigger_match",
            "context_match",
            "capability_match",
            "outcome_match",
            "safety_match",
        ):
            with self.subTest(key=key):
                task = valid_task()
                match = copy.deepcopy(self.match())
                match[key] = False
                task["specialized_match"] = match

                decision = classify_task(
                    task, registered_workflows={"WF-SPECIAL@1.0"}
                )

                self.assertEqual(decision.route, "tree")


if __name__ == "__main__":
    unittest.main()
