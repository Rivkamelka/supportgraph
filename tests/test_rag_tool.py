from __future__ import annotations

from langchain_core.documents import Document

import app.tools.rag_tool as rag_tool_module
from app.tools.rag_tool import policy_search_tool


def test_policy_search_formats_passages_with_source(monkeypatch):
    monkeypatch.setattr(
        rag_tool_module,
        "search_policies",
        lambda query: [Document(page_content="Refunds take 5-7 business days.", metadata={"source": "policy_returns.md"})],
    )

    result = policy_search_tool.invoke({"query": "how long does a refund take"})

    assert "policy_returns.md" in result
    assert "5-7 business days" in result


def test_policy_search_reports_no_matches(monkeypatch):
    monkeypatch.setattr(rag_tool_module, "search_policies", lambda query: [])

    result = policy_search_tool.invoke({"query": "asdkjhasd"})

    assert "No relevant policy passage found" in result


def test_policy_search_degrades_gracefully_on_qdrant_error(monkeypatch):
    def boom(query):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(rag_tool_module, "search_policies", boom)

    result = policy_search_tool.invoke({"query": "return policy"})

    assert "Error reaching the policy knowledge base" in result
