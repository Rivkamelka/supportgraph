from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api import routes_chat, routes_health, routes_ingest
from app.rag.ingest import run_ingest

logger = logging.getLogger("supportgraph")

STATIC_DIR = Path(__file__).resolve().parent / "static"


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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Any exception a route didn't already turn into an HTTPException
    lands here: logged with a full traceback server-side, but the client
    only ever sees a generic message -- never a raw stack trace, which
    could leak internal file paths or query shapes."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", include_in_schema=False)
def root():
    """A small interactive landing page (see app/static/index.html):
    a live component-status panel plus a form that calls /api/ask
    directly, so the project can be shown off without a separate
    frontend. The full machine-readable API stays at /docs."""
    return FileResponse(STATIC_DIR / "index.html")
