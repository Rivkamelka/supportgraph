from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import IngestResponse
from app.rag.ingest import run_ingest

router = APIRouter(tags=["ingest"])


@router.post("/api/documents/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    try:
        n_docs, n_chunks = run_ingest()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not reach Qdrant: {exc}") from exc
    return IngestResponse(documents_indexed=n_docs, chunks_indexed=n_chunks, collection=settings.qdrant_collection)
