from __future__ import annotations

from fastapi import APIRouter

from app.agent.graph import get_compiled_graph
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/api/ask", response_model=ChatResponse)
def ask(request: ChatRequest) -> ChatResponse:
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
