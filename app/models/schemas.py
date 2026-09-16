"""Pydantic models shared across the API and the agent graph."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=2000, description="The customer's question, in natural language."
    )
    customer_id: int | None = Field(
        default=None,
        ge=1,
        description="Known customer id, if the question is about a specific account (order, loyalty, etc).",
    )


class ChatResponse(BaseModel):
    answer: str
    routes: list[str] = Field(default_factory=list, description="Which data sources were consulted.")
    sources: list[str] = Field(default_factory=list, description="Human-readable provenance for the answer.")
    demo_mode: bool = Field(description="Whether the answer was produced by the mock LLM (no API key configured).")


class RouteDecision(BaseModel):
    """Structured output shape asked of a real LLM during intent routing.

    Only used when a real provider + key is configured; the demo-mode
    heuristic router (see app/agent/router.py) never touches this model,
    but keeps the exact same field names so both paths are interchangeable
    from the graph's point of view.
    """

    use_sql: bool = Field(description="True if the question is about a specific order, purchase or shipment status.")
    use_mongo: bool = Field(description="True if the question is about a product's catalog details, specs or availability.")
    use_oracle: bool = Field(description="True if the question is about a customer's loyalty tier or risk score.")
    use_rag: bool = Field(description="True if the question is about a policy: returns, shipping, warranty, FAQ.")


class IngestResponse(BaseModel):
    documents_indexed: int
    chunks_indexed: int
    collection: str


class HealthStatus(BaseModel):
    status: str
    demo_mode: bool
    llm_provider: str
    embedding_provider: str
    mysql: str
    mongo: str
    oracle: str
    qdrant: str
