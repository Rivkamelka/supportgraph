"""LangChain Tool wrapper around the RAG retriever -- policy documents."""

from __future__ import annotations

from langchain_core.tools import tool

from app.rag.retriever import search_policies


@tool
def policy_search_tool(query: str) -> str:
    """Search the store's policy documents (returns, shipping, FAQ) for
    passages relevant to the question."""
    try:
        docs = search_policies(query)
    except Exception as exc:  # pragma: no cover - depends on live Qdrant
        return f"Error reaching the policy knowledge base: {exc}"

    if not docs:
        return "No relevant policy passage found."

    passages = "; ".join(f"({d.metadata.get('source', 'unknown')}) {d.page_content}" for d in docs)
    return passages
