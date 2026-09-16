"""Intent classification: decides which data sources a question needs.

Two paths, chosen by app.config.settings.is_demo_mode:

- Demo mode (default, no API key): a keyword heuristic, the same style of
  approach used for Insight's heuristic planner -- fast, free, and good
  enough for a fixed demo vocabulary.
- Real LLM configured: the chat model's structured-output mode fills a
  RouteDecision pydantic model directly, so the routing becomes an actual
  LLM decision instead of keyword matching.

Either path returns the same shape (`{"routes": [...]}`), so the rest of
the graph never needs to know which one ran.
"""

from __future__ import annotations

import re

from app.agent.state import AgentState
from app.config import settings
from app.llm.provider import get_chat_model
from app.models.schemas import RouteDecision

_SQL_WORDS = re.compile(r"\border|orders|commande|shipment|shipped|delivery status|purchase\b", re.IGNORECASE)
_MONGO_WORDS = re.compile(r"\bproduct|catalog|catalogue|stock|price of|specs?|available\b", re.IGNORECASE)
_ORACLE_WORDS = re.compile(r"\bloyalty|tier|vip|risk score|fidélité|fidelite\b", re.IGNORECASE)
_RAG_WORDS = re.compile(
    r"\bpolicy|return|refund|warranty|shipping|delivery time|faq|exchange|damaged|lost package\b",
    re.IGNORECASE,
)


def _heuristic_routes(question: str) -> list[str]:
    routes = []
    if _SQL_WORDS.search(question):
        routes.append("sql")
    if _MONGO_WORDS.search(question):
        routes.append("mongo")
    if _ORACLE_WORDS.search(question):
        routes.append("oracle")
    if _RAG_WORDS.search(question):
        routes.append("rag")
    if not routes:
        # Fallback: most unmatched questions in an e-commerce support
        # context are "can I / how do I / what if" policy questions.
        routes.append("rag")
    return routes


def _llm_routes(question: str) -> list[str]:
    llm = get_chat_model().with_structured_output(RouteDecision)
    decision: RouteDecision = llm.invoke(
        "Classify which internal systems are needed to answer this customer support "
        f"question. Question: {question!r}"
    )
    routes = []
    if decision.use_sql:
        routes.append("sql")
    if decision.use_mongo:
        routes.append("mongo")
    if decision.use_oracle:
        routes.append("oracle")
    if decision.use_rag:
        routes.append("rag")
    return routes or ["rag"]


def classify_intent(state: AgentState) -> dict:
    question = state["question"]
    if settings.is_demo_mode:
        routes = _heuristic_routes(question)
    else:
        try:
            routes = _llm_routes(question)
        except Exception:
            # A live-LLM failure (rate limit, network) should degrade to
            # the heuristic rather than break the whole request.
            routes = _heuristic_routes(question)
    return {"routes": routes}
