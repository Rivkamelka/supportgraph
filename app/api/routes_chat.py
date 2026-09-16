from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.agent.graph import get_compiled_graph
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.rate_limit import is_rate_limited

router = APIRouter(tags=["chat"])


def _client_key(request: Request) -> str:
    # Vercel (and most PaaS proxies) put the real client IP in
    # X-Forwarded-For; request.client.host would otherwise just be the
    # proxy's own address.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/api/ask", response_model=ChatResponse)
def ask(request: ChatRequest, http_request: Request) -> ChatResponse:
    limited, retry_after = is_rate_limited(_client_key(http_request))
    if limited:
        raise HTTPException(
            status_code=429,
            detail="Too many requests -- please wait a moment before asking again.",
            headers={"Retry-After": str(retry_after)},
        )

    graph = get_compiled_graph()
    result = graph.invoke(
        {
            "question": request.question,
            "customer_id": request.customer_id,
            "results": [],
        }
    )
    return ChatResponse(
        answer=result.get("answer", ""),
        routes=result.get("routes", []),
        sources=result.get("sources", []),
        demo_mode=settings.is_demo_mode,
    )
