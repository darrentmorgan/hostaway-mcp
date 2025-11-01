"""Tests for dependency resolution logic in orchestrator.sh"""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def config_dir():
    """Path to automation config directory."""
    return Path(__file__).parent.parent.parent / ".automation" / "config"


@pytest.fixture
def dependency_graph(config_dir):
    """Load the dependency graph configuration."""
    with (config_dir / "dependency-graph.yaml").open() as f:
        return yaml.safe_load(f)


def test_dependency_graph_structure(dependency_graph):
    """Test that dependency graph has required structure."""
    assert "nodes" in dependency_graph
    assert "edges" in dependency_graph
    assert "execution_order" in dependency_graph


def test_all_nodes_present(dependency_graph):
    """Test that all 7 fixes are present in nodes."""
    nodes = dependency_graph["nodes"]
    assert len(nodes) == 7

    expected_nodes = [
        "fix-1-service-prefixes",
        "fix-2-tool-annotations",
        "fix-3-error-messages",
        "fix-4-response-formats",
        "imp-1-tool-descriptions",
        "imp-2-input-validation",
        "imp-3-character-limit",
    ]

    assert set(nodes) == set(expected_nodes)


def test_execution_order_covers_all_nodes(dependency_graph):
    """Test that execution order includes all nodes exactly once."""
    nodes = set(dependency_graph["nodes"])
    execution_order = dependency_graph["execution_order"]

    # Flatten execution waves
    all_in_order = []
    for wave in execution_order:
        all_in_order.extend(wave)

    assert set(all_in_order) == nodes, "Execution order must include all nodes"
    assert len(all_in_order) == len(nodes), "No node should appear twice"


def test_fix_4_dependencies(dependency_graph):
    """Test that Fix 4 has correct dependencies (Fix 1 and Fix 3)."""
    edges = dependency_graph["edges"]

    # Find dependencies for fix-4
    fix_4_deps = [edge["from"] for edge in edges if edge["to"] == "fix-4-response-formats"]

    assert "fix-1-service-prefixes" in fix_4_deps
    assert "fix-3-error-messages" in fix_4_deps


def test_wave_1_is_independent(dependency_graph):
    """Test that Wave 1 fixes have no dependencies on each other."""
    execution_order = dependency_graph["execution_order"]
    wave_1 = set(execution_order[0])
    edges = dependency_graph["edges"]

    # Check that no Wave 1 fix depends on another Wave 1 fix
    for edge in edges:
        if edge["to"] in wave_1:
            assert (
                edge["from"] not in wave_1
            ), f"{edge['to']} in Wave 1 should not depend on {edge['from']} also in Wave 1"


def test_wave_2_depends_on_wave_1(dependency_graph):
    """Test that Wave 2 (Fix 4) depends only on Wave 1 fixes."""
    execution_order = dependency_graph["execution_order"]

    # Should be 2 waves
    assert len(execution_order) == 2, "Should have exactly 2 execution waves"

    wave_1 = set(execution_order[0])
    wave_2 = set(execution_order[1])
    edges = dependency_graph["edges"]

    # Wave 2 should only be Fix 4
    assert wave_2 == {"fix-4-response-formats"}

    # Fix 4 dependencies should all be in Wave 1
    fix_4_deps = [edge["from"] for edge in edges if edge["to"] == "fix-4-response-formats"]
    for dep in fix_4_deps:
        assert dep in wave_1, f"Fix 4 dependency {dep} must be in Wave 1"


def test_no_circular_dependencies(dependency_graph):
    """Test that there are no circular dependencies."""
    edges = dependency_graph["edges"]
    nodes = dependency_graph["nodes"]

    # Build adjacency list
    graph = {node: [] for node in nodes}
    in_degree = dict.fromkeys(nodes, 0)

    for edge in edges:
        graph[edge["from"]].append(edge["to"])
        in_degree[edge["to"]] += 1

    # Kahn's algorithm for cycle detection
    queue = [node for node in nodes if in_degree[node] == 0]
    processed = []

    while queue:
        node = queue.pop(0)
        processed.append(node)

        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If we processed all nodes, there's no cycle
    assert len(processed) == len(nodes), "Circular dependency detected!"


def test_execution_waves_match_dependencies(dependency_graph):
    """Test that execution waves respect dependency ordering."""
    execution_order = dependency_graph["execution_order"]
    edges = dependency_graph["edges"]

    # Build map of which wave each fix is in
    wave_map = {}
    for wave_idx, wave in enumerate(execution_order):
        for fix in wave:
            wave_map[fix] = wave_idx

    # For each edge, verify dependency is in earlier or same wave
    for edge in edges:
        from_wave = wave_map[edge["from"]]
        to_wave = wave_map[edge["to"]]

        assert (
            from_wave < to_wave
        ), f"{edge['to']} (wave {to_wave}) depends on {edge['from']} (wave {from_wave}), but they're in wrong order"


@pytest.mark.skip(reason="Integration test - requires actual execution")
def test_orchestrator_respects_dependencies():
    """Integration test: verify orchestrator executes in correct order."""
    # This would require running orchestrator.sh and checking logs
    # Skipped for unit tests, should be tested in integration suite
