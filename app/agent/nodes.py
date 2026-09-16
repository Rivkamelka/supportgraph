"""The four data-source nodes and the final synthesis node.

Each run_* node is intentionally dumb: pull whatever id it needs out of
state, call exactly one tool, append one ToolFinding to `results`. All of
the actual "what does this mean" work happens once, in `synthesize`, which
hands the collected findings to the chat model (mock or real) to phrase
into a single answer -- the same plan/execute separation used throughout
this project and in the Insight project before it.
"""

from __future__ import annotations

import re

from langchain_core.messages import HumanMessage

from app.agent.state import AgentState
from app.llm.provider import get_chat_model
from app.tools.mongo_tool import product_search_tool
from app.tools.oracle_tool import loyalty_lookup_tool
from app.tools.rag_tool import policy_search_tool
from app.tools.sql_tool import order_lookup_tool

_CUSTOMER_ID_RE = re.compile(r"customer\s*#?\s*(\d+)", re.IGNORECASE)


def _resolve_customer_id(state: AgentState) -> int | None:
    if state.get("customer_id") is not None:
        return state["customer_id"]
    match = _CUSTOMER_ID_RE.search(state["question"])
    return int(match.group(1)) if match else None


def run_sql(state: AgentState) -> dict:
    content = order_lookup_tool.invoke({"question": state["question"]})
    return {"results": [{"source": "mysql", "content": content}]}


def run_mongo(state: AgentState) -> dict:
    content = product_search_tool.invoke({"query": state["question"]})
    return {"results": [{"source": "mongo", "content": content}]}


def run_oracle(state: AgentState) -> dict:
    customer_id = _resolve_customer_id(state)
    if customer_id is None:
        content = "No customer id was provided or found in the question, so loyalty status could not be looked up."
    else:
        content = loyalty_lookup_tool.invoke({"customer_id": customer_id})
    return {"results": [{"source": "oracle", "content": content}]}


def run_rag(state: AgentState) -> dict:
    content = policy_search_tool.invoke({"query": state["question"]})
    return {"results": [{"source": "rag", "content": content}]}


def synthesize(state: AgentState) -> dict:
    results = state.get("results", [])
    findings_block = "\n".join(f"[{r['source']}] {r['content']}" for r in results)
    prompt = (
        "You are an e-commerce customer support assistant. Answer the customer's "
        "question in one or two short, friendly sentences, using ONLY the findings "
        "below. If the findings don't answer the question, say so honestly.\n\n"
        f"Question: {state['question']}\n\nFindings:\n{findings_block}"
    )
    llm = get_chat_model()
    response = llm.invoke([HumanMessage(content=prompt)])
    sources = [r["source"] for r in results]
    return {"answer": str(response.content), "sources": sources}
