"""Directed acyclic graph helpers shared by VGTREE validators."""

from __future__ import annotations

from collections import deque


def has_cycle(graph: dict[str, list[str]]) -> bool:
    """Return whether the known nodes in *graph* contain a dependency cycle."""

    indegree = {node: 0 for node in graph}
    dependents: dict[str, list[str]] = {node: [] for node in graph}
    for node, dependencies in graph.items():
        for dependency in dependencies:
            if dependency not in graph:
                continue
            indegree[node] += 1
            dependents[dependency].append(node)

    ready = deque(node for node, count in indegree.items() if count == 0)
    visited = 0
    while ready:
        node = ready.popleft()
        visited += 1
        for dependent in dependents[node]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
    return visited != len(graph)
