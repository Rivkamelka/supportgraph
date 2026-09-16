# ADR 0002: Demo mode with zero API keys, real providers behind config

## Status
Accepted

## Context
The project needs to be runnable, demoable, and testable with zero cost
and zero external account setup, while still genuinely wiring up
LangChain's real chat-model and embeddings classes so the integration
isn't just a stub.

## Decision
Two provider abstractions (`app/llm/provider.py`, `app/llm/embeddings.py`)
each expose a single `get_*()` factory that reads `app.config.settings`
and returns:

- `MockChatModel` (subclasses `langchain_core.language_models.BaseChatModel`)
  when no real key is configured -- a deterministic model that phrases
  already-computed tool findings into a sentence, rather than trying to
  fake reasoning.
- `HashingEmbeddings` (subclasses `langchain_core.embeddings.Embeddings`)
  when no real key is configured -- a stable feature-hashing embedding
  (`md5`-seeded, not Python's randomised built-in `hash()`) good enough
  to rank a small, fixed policy corpus.
- `ChatOpenAI` / `ChatAnthropic` / `OpenAIEmbeddings` when a real
  `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is present and selected via
  `LLM_PROVIDER` / `EMBEDDING_PROVIDER`.

Because both mock classes implement the real LangChain base classes, every
other part of the codebase (`app/agent/nodes.py`, `app/agent/router.py`,
`app/rag/ingest.py`) calls `.invoke(...)`, `.with_structured_output(...)`,
`.embed_documents(...)` exactly as it would against a real provider.
Switching out of demo mode is a `.env` change, not a code change.

## Consequences
- The whole stack (FastAPI, LangGraph, Qdrant, MySQL, Mongo, Oracle) can
  be demoed end to end for $0.
- `classify_intent` still has two code paths (heuristic vs. structured
  LLM output) because routing quality genuinely differs; everything
  downstream of routing is provider-agnostic.
