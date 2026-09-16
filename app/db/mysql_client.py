"""MySQL client: the transactional "orders" system of record.

Kept deliberately thin and read-oriented -- the support agent looks orders
up, it never writes to them. Every function returns plain dicts (never
raises out of the tool layer) so a tool node can catch DB-down situations
gracefully instead of crashing the whole graph run.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from app.config import settings


@contextmanager
def get_connection() -> Iterator[Any]:
    # Imported lazily so a missing/incompatible driver only breaks the one
    # call that needs it (caught by the tool layer / health check) instead
    # of crashing the whole app at import time -- see ADR-ready note in
    # app/rag/ingest.py for why this matters on a serverless deploy.
    import pymysql
    import pymysql.cursors

    conn = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=3,
    )
    try:
        yield conn
    finally:
        conn.close()


def get_order(order_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.id AS order_id, o.customer_id,
                       CONCAT(c.first_name, ' ', c.last_name) AS full_name,
                       o.status, o.order_date, o.total_amount
                FROM orders o
                JOIN customers c ON c.id = o.customer_id
                WHERE o.id = %s
                """,
                (order_id,),
            )
            order = cur.fetchone()
            if order is None:
                return None
            cur.execute(
                "SELECT product_sku, quantity, unit_price FROM order_items WHERE order_id = %s",
                (order_id,),
            )
            order["items"] = cur.fetchall()
            return order


def get_customer_orders(customer_id: int, limit: int = 5) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id AS order_id, status, order_date, total_amount
                FROM orders
                WHERE customer_id = %s
                ORDER BY order_date DESC
                LIMIT %s
                """,
                (customer_id, limit),
            )
            return cur.fetchall()


def find_customer_by_name(name_fragment: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id AS customer_id, CONCAT(first_name, ' ', last_name) AS full_name, email
                FROM customers
                WHERE CONCAT(first_name, ' ', last_name) LIKE %s
                LIMIT 1
                """,
                (f"%{name_fragment}%",),
            )
            return cur.fetchone()
