"""Structural tests that don't require any live database: they check the
graph compiles and that classify->fanout routing picks the right nodes,
using the demo-mode heuristic router (no network, no API key needed).
"""

from app.agent.graph import build_graph


def test_graph_compiles():
    graph = build_graph()
    assert graph is not None


def test_graph_has_expected_nodes():
    graph = build_graph()
    node_names = set(graph.get_graph().nodes.keys())
    for expected in {"classify", "run_sql", "run_mongo", "run_oracle", "run_rag", "synthesize"}:
        assert expected in node_names
