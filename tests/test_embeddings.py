from app.llm.embeddings import HashingEmbeddings


def test_hashing_embeddings_is_deterministic():
    emb = HashingEmbeddings(dims=64)
    v1 = emb.embed_query("can I return a broken headset")
    v2 = emb.embed_query("can I return a broken headset")
    assert v1 == v2


def test_hashing_embeddings_is_normalised():
    emb = HashingEmbeddings(dims=64)
    v = emb.embed_query("standing desk shipping time")
    norm = sum(x * x for x in v) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_hashing_embeddings_differs_for_different_text():
    emb = HashingEmbeddings(dims=64)
    v1 = emb.embed_query("return policy")
    v2 = emb.embed_query("shipping delay furniture")
    assert v1 != v2


def test_embed_documents_matches_embed_query():
    emb = HashingEmbeddings(dims=64)
    text = "loyalty tier calculation"
    assert emb.embed_documents([text])[0] == emb.embed_query(text)
