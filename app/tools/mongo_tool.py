"""LangChain Tool wrapper around the MongoDB client -- product catalog."""

from __future__ import annotations

from langchain_core.tools import tool

from app.db import mongo_client


@tool
def product_search_tool(query: str) -> str:
    """Search the product catalog by free-text query (product name,
    category, or feature keyword like "wireless" or "adjustable")."""
    try:
        products = mongo_client.search_products(query)
    except Exception as exc:  # pragma: no cover - depends on live DB
        return f"Error reaching the product catalog: {exc}"

    if not products:
        return f"No products found matching '{query}'."

    lines = []
    for p in products:
        attrs = ", ".join(f"{k}={v}" for k, v in (p.get("attributes") or {}).items())
        lines.append(f"{p['name']} (SKU {p['sku']}, ${p['price']:.2f}, {p['category']}" + (f", {attrs}" if attrs else "") + ")")
    return "Matching products: " + "; ".join(lines) + "."
