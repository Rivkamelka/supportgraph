"""Loads the knowledge_base/*.md policy documents, chunks them, embeds
them (mock hashing or real, per app/llm/embeddings.py), and upserts them
into Qdrant through LangChain's QdrantVectorStore.

Run automatically once at app startup (see app/main.py's lifespan), and
exposed again via POST /api/documents/ingest so new documents can be
added without a restart.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from app.config import settings
from app.llm.embeddings import get_embeddings

# qdrant_client / langchain_qdrant are imported lazily, inside the
# functions below, rather than at module level. This module is imported
# eagerly by app/main.py at startup (for the RAG-ingest lifespan hook), so
# a module-level import here would mean any install/runtime incompatibility
# with these packages (seen in practice on some serverless Python
# sandboxes, e.g. Vercel) crashes the *entire app* before it can even
# start serving -- rather than just this one feature degrading, which is
# what every other tool in this project already does gracefully.

KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"


def _chunk_markdown(text: str, source: str) -> list[Document]:
    """Splits on blank-line-separated paragraphs. The knowledge base here
    is short, hand-written policy prose, so a simple paragraph split keeps
    each chunk self-contained and human-readable in citations -- no need
    for a token-aware splitter at this scale."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [Document(page_content=p, metadata={"source": source}) for p in paragraphs]


def load_documents() -> list[Document]:
    docs: list[Document] = []
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.extend(_chunk_markdown(text, source=path.name))
    return docs


def get_qdrant_client() -> Any:
    from qdrant_client import QdrantClient

    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(client: Any, vector_size: int) -> None:
    from qdrant_client.http.models import Distance, VectorParams

    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def run_ingest() -> tuple[int, int]:
    """Returns (documents_indexed, chunks_indexed)."""
    from langchain_qdrant import QdrantVectorStore

    embeddings = get_embeddings()
    docs = load_documents()
    if not docs:
        return (0, 0)

    probe_vector = embeddings.embed_query("probe")
    client = get_qdrant_client()
    ensure_collection(client, vector_size=len(probe_vector))

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )
    vectorstore.add_documents(docs)

    n_files = len({d.metadata["source"] for d in docs})
    return (n_files, len(docs))
