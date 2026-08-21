from __future__ import annotations

import unittest

from vgtree.dag import has_cycle


class DagTests(unittest.TestCase):
    def test_acyclic_graph_returns_false(self) -> None:
        self.assertFalse(has_cycle({"build": [], "deploy": ["build"]}))

    def test_cycle_returns_true(self) -> None:
        self.assertTrue(has_cycle({"a": ["b"], "b": ["a"]}))

    def test_thousand_node_chain_is_iterative(self) -> None:
        graph = {
            f"b-{index}": [f"b-{index - 1}"] if index else []
            for index in range(1000)
        }
        self.assertFalse(has_cycle(graph))


if __name__ == "__main__":
    unittest.main()
