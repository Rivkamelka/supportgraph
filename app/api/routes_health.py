"""Health + direct demo endpoints, one per data source, so each piece of
the stack (MySQL, Mongo, Oracle, Qdrant) can be shown working
independently of the LLM/agent layer -- useful in a demo or interview to
prove each connection is real.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.db import mongo_client, mysql_client, oracle_client
from app.models.schemas import HealthStatus
from app.rag.ingest import get_qdrant_client

router = APIRouter(tags=["health"])


def _check(fn) -> str:
    try:
        fn()
        return "ok"
    except Exception as exc:  # pragma: no cover - depends on live services
        return f"unreachable ({exc.__class__.__name__})"


@router.get("/api/health", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(
        status="ok",
        demo_mode=settings.is_demo_mode,
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
        mysql=_check(lambda: mysql_client.get_order(-1)),
        mongo=_check(lambda: mongo_client.get_database().list_collection_names()),
        oracle=_check(lambda: oracle_client.get_loyalty(-1)),
        qdrant=_check(lambda: get_qdrant_client().get_collections()),
    )


@router.get("/api/orders/{order_id}")
def get_order(order_id: int):
    order = mysql_client.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/api/products/search")
def search_products(q: str):
    return mongo_client.search_products(q)


@router.get("/api/customers/{customer_id}/loyalty")
def get_loyalty(customer_id: int):
    loyalty = oracle_client.get_loyalty(customer_id)
    if loyalty is None:
        raise HTTPException(status_code=404, detail="No loyalty record for this customer")
    return loyalty
