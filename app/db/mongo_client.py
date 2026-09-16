"""MongoDB client: the semi-structured "catalog + session logs" store.

Products have category-specific attributes (a monitor has a refresh rate,
a chair does not) which is exactly the kind of schema-per-document shape
that is awkward in a relational table and natural in Mongo.
"""

from __future__ import annotations

from typing import Any

from app.config import settings

_client: Any = None


def get_client() -> Any:
    # Imported lazily -- see app/db/mysql_client.py's get_connection() for why.
    global _client
    if _client is None:
        from pymongo import MongoClient

        _client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
    return _client


def get_database():
    return get_client()[settings.mongo_database]


def products_collection() -> Any:
    return get_database()["products"]


def support_sessions_collection() -> Any:
    return get_database()["support_sessions"]


def search_products(query: str, limit: int = 5) -> list[dict[str, Any]]:
    coll = products_collection()
    try:
        cursor = coll.find({"$text": {"$search": query}}, {"score": {"$meta": "textScore"}})
        cursor = cursor.sort([("score", {"$meta": "textScore"})]).limit(limit)
        results = list(cursor)
        if results:
            return results
    except Exception:
        pass
    # Fallback: naive substring match on name/category, for short or
    # stop-word-only queries the text index would return nothing for.
    regex = {"$regex": query, "$options": "i"}
    return list(coll.find({"$or": [{"name": regex}, {"category": regex}]}).limit(limit))


def get_product_by_sku(sku: str) -> dict[str, Any] | None:
    return products_collection().find_one({"sku": sku})


def get_support_sessions(customer_id: int) -> list[dict[str, Any]]:
    return list(support_sessions_collection().find({"customer_id": customer_id}))
