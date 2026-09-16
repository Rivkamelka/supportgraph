from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_chat, routes_health, routes_ingest
from app.config import settings
from app.rag.ingest import run_ingest

logger = logging.getLogger("supportgraph")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort: if Qdrant isn't up yet (e.g. docker compose is still
    # starting), the app still boots -- /api/documents/ingest can be
    # called again manually once it's ready.
    try:
        n_docs, n_chunks = run_ingest()
        logger.info("RAG ingest at startup: %s documents, %s chunks", n_docs, n_chunks)
    except Exception as exc:
        logger.warning("RAG ingest at startup failed (will retry via /api/documents/ingest): %s", exc)
    yield


app = FastAPI(
    title="SupportGraph",
    description="LangGraph-orchestrated e-commerce customer support agent (MySQL + MongoDB + Oracle PL/SQL + RAG).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router)
app.include_router(routes_chat.router)
app.include_router(routes_ingest.router)


@app.get("/")
def root():
    return {
        "name": "SupportGraph",
        "demo_mode": settings.is_demo_mode,
        "docs": "/docs",
    }
