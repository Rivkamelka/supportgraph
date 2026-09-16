"""Builds a LangChain retriever over the Qdrant collection populated by
app/rag/ingest.py. This is the piece the rag_tool wraps as a LangChain
Tool for the agent graph.
"""

from __future__ import annotations

from langchain_core.documents import Document

from app.config import settings
from app.llm.embeddings import get_embeddings
from app.rag.ingest import get_qdrant_client


def get_retriever(k: int = 3):
    from langchain_qdrant import QdrantVectorStore

    vectorstore = QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_collection,
        embedding=get_embeddings(),
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})


def search_policies(query: str, k: int = 3) -> list[Document]:
    return get_retriever(k=k).invoke(query)
