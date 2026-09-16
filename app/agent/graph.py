"""Wires the AgentState nodes into a LangGraph StateGraph.

classify -> [fan-out via Send, one branch per selected route] -> synthesize

The Send API (langgraph.types.Send) is what lets `classify`'s output
decide, at runtime, exactly which of the four data-source nodes actually
execute -- a question that only needs the RAG policy lookup never touches
MySQL/Mongo/Oracle at all, while a question needing two sources runs both
branches concurrently.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agent import nodes
from app.agent.router import classify_intent
from app.agent.state import AgentState

_ALL_ROUTE_NODES = ["run_sql", "run_mongo", "run_oracle", "run_rag"]


def _fanout(state: AgentState):
    routes = state.get("routes") or []
    sends = [Send(f"run_{route}", state) for route in routes if f"run_{route}" in _ALL_ROUTE_NODES]
    return sends if sends else "synthesize"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_intent)
    graph.add_node("run_sql", nodes.run_sql)
    graph.add_node("run_mongo", nodes.run_mongo)
    graph.add_node("run_oracle", nodes.run_oracle)
    graph.add_node("run_rag", nodes.run_rag)
    graph.add_node("synthesize", nodes.synthesize)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", _fanout, [*_ALL_ROUTE_NODES, "synthesize"])
    for node_name in _ALL_ROUTE_NODES:
        graph.add_edge(node_name, "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


@lru_cache
def get_compiled_graph():
    return build_graph()
