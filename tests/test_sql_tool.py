from __future__ import annotations

from app.db import mysql_client
from app.tools.sql_tool import customer_orders_tool, order_lookup_tool


def test_order_lookup_returns_formatted_summary(monkeypatch):
    monkeypatch.setattr(
        mysql_client,
        "get_order",
        lambda order_id: {
            "order_id": order_id,
            "full_name": "Marc Dupont",
            "status": "delivered",
            "order_date": "2023-01-10",
            "total_amount": 45.0,
            "items": [{"quantity": 1, "product_sku": "KEY-100", "unit_price": 45.0}],
        },
    )

    result = order_lookup_tool.invoke({"question": "what's the status of order 6?"})

    assert "Marc Dupont" in result
    assert "delivered" in result
    assert "KEY-100" in result


def test_order_lookup_reports_missing_order(monkeypatch):
    monkeypatch.setattr(mysql_client, "get_order", lambda order_id: None)

    result = order_lookup_tool.invoke({"question": "order 999999"})

    assert "No order found" in result


def test_order_lookup_without_an_order_id_asks_for_one():
    result = order_lookup_tool.invoke({"question": "what's my order status?"})

    assert "No numeric order id" in result


def test_order_lookup_degrades_gracefully_on_db_error(monkeypatch):
    def boom(order_id):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(mysql_client, "get_order", boom)

    result = order_lookup_tool.invoke({"question": "order 6"})

    assert "Error reaching the orders database" in result


def test_customer_orders_tool_lists_recent_orders(monkeypatch):
    monkeypatch.setattr(
        mysql_client,
        "get_customer_orders",
        lambda customer_id, limit=5: [
            {"order_id": 1, "status": "delivered", "total_amount": 129.9},
            {"order_id": 2, "status": "returned", "total_amount": 59.0},
        ],
    )

    result = customer_orders_tool.invoke({"customer_id": 1})

    assert "#1" in result and "#2" in result
    assert "delivered" in result and "returned" in result


def test_customer_orders_tool_reports_no_orders(monkeypatch):
    monkeypatch.setattr(mysql_client, "get_customer_orders", lambda customer_id, limit=5: [])

    result = customer_orders_tool.invoke({"customer_id": 42})

    assert "No orders found" in result
