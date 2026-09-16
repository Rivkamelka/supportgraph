"""LangChain Tool wrapper around the MySQL client -- orders."""

from __future__ import annotations

import re

from langchain_core.tools import tool

from app.db import mysql_client

_ORDER_ID_RE = re.compile(r"\b(\d{1,10})\b")


@tool
def order_lookup_tool(question: str) -> str:
    """Look up an order's status, date, total and line items. The input
    should contain the numeric order id somewhere in the text (e.g.
    "what's the status of order 1042?")."""
    match = _ORDER_ID_RE.search(question)
    if not match:
        return "No numeric order id found in the question; ask the customer for their order number."
    order_id = int(match.group(1))
    try:
        order = mysql_client.get_order(order_id)
    except Exception as exc:  # pragma: no cover - depends on live DB
        return f"Error reaching the orders database: {exc}"

    if order is None:
        return f"No order found with id {order_id}."

    items = ", ".join(f"{it['quantity']}x {it['product_sku']}" for it in order["items"])
    return (
        f"Order {order['order_id']} for {order['full_name']} is currently '{order['status']}' "
        f"(placed {order['order_date']}), total ${order['total_amount']:.2f}. Items: {items}."
    )


@tool
def customer_orders_tool(customer_id: int) -> str:
    """List the most recent orders for a given numeric customer id."""
    try:
        orders = mysql_client.get_customer_orders(customer_id)
    except Exception as exc:  # pragma: no cover
        return f"Error reaching the orders database: {exc}"

    if not orders:
        return f"No orders found for customer {customer_id}."

    lines = [f"#{o['order_id']} ({o['status']}, ${o['total_amount']:.2f})" for o in orders]
    return f"Recent orders for customer {customer_id}: " + "; ".join(lines) + "."
