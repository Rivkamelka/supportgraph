"""Embeddings abstraction, mirroring app/llm/provider.py.

HashingEmbeddings is the demo-mode default: a deterministic, dependency-free
feature-hashing embedding (the classic "hashing trick"). It costs nothing,
needs no API key, and is stable across process restarts (it uses md5, not
Python's randomized built-in hash()), which is what makes it good enough
for a small, fixed knowledge base of policy documents. Swapping in
OpenAIEmbeddings is a one-line config change (EMBEDDING_PROVIDER=openai).
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import List

from langchain_core.embeddings import Embeddings

from app.config import settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbeddings(Embeddings):
    def __init__(self, dims: int = 256):
        self.dims = dims

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dims
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            bucket = int(digest, 16) % self.dims
            # A second, independent hash flips the sign so unrelated words
            # don't all push the vector in the same direction (a standard
            # refinement of plain feature hashing).
            sign_digest = hashlib.md5((token + "#sign").encode("utf-8")).hexdigest()
            sign = 1.0 if int(sign_digest, 16) % 2 == 0 else -1.0
            vec[bucket] += sign

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def get_embeddings() -> Embeddings:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(api_key=settings.openai_api_key)
    return HashingEmbeddings()
