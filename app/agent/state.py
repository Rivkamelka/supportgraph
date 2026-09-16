"""Shared state schema for the LangGraph agent.

`results` uses the `operator.add` reducer so that when the graph fans out
to several `run_*` nodes in parallel (via the Send API, see
app/agent/graph.py), each node's single-item list is concatenated onto the
shared state instead of overwriting it -- the standard LangGraph pattern
for parallel branches that all write to the same field.
"""

from __future__ import annotations

import operator
from typing import Annotated, Optional

# LangGraph (via Pydantic v2) needs typing_extensions.TypedDict rather than
# typing.TypedDict on Python < 3.12, or schema generation for introspection
# (e.g. graph.get_graph()) breaks -- see
# https://errors.pydantic.dev/2.9/u/typed-dict-version
from typing_extensions import TypedDict


class ToolFinding(TypedDict):
    source: str
    content: str


class AgentState(TypedDict, total=False):
    question: str
    customer_id: Optional[int]
    routes: list[str]
    results: Annotated[list[ToolFinding], operator.add]
    answer: str
    sources: list[str]
