from __future__ import annotations

from app.db import mongo_client
from app.tools.mongo_tool import product_search_tool


def test_product_search_formats_results_with_attributes(monkeypatch):
    monkeypatch.setattr(
        mongo_client,
        "search_products",
        lambda query, limit=5: [
            {
                "sku": "MON-270",
                "name": 'Monitor 27" QHD',
                "price": 249.5,
                "category": "displays",
                "attributes": {"refresh_hz": 75},
            }
        ],
    )

    result = product_search_tool.invoke({"query": "monitor"})

    assert "MON-270" in result
    assert "refresh_hz=75" in result


def test_product_search_reports_no_matches(monkeypatch):
    monkeypatch.setattr(mongo_client, "search_products", lambda query, limit=5: [])

    result = product_search_tool.invoke({"query": "gaming chair"})

    assert "No products found" in result


def test_product_search_degrades_gracefully_on_db_error(monkeypatch):
    def boom(query, limit=5):
        raise RuntimeError("server selection timeout")

    monkeypatch.setattr(mongo_client, "search_products", boom)

    result = product_search_tool.invoke({"query": "keyboard"})

    assert "Error reaching the product catalog" in result
