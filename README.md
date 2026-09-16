# SupportGraph

[![CI](https://github.com/Rivkamelka/supportgraph/actions/workflows/ci.yml/badge.svg)](https://github.com/Rivkamelka/supportgraph/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A LangGraph-orchestrated e-commerce customer support agent, built to
demonstrate a realistic multi-database AI-agent architecture: **LangChain
+ LangGraph + RAG/VectorDB + LLMs + AI Agents** on top of **MySQL +
MongoDB + Oracle PL/SQL**, exposed through a **FastAPI REST API**.

It runs end to end for $0: no OpenAI/Anthropic API key required. Demo mode
uses a deterministic mock chat model and a deterministic hashing-based
embedding, both real LangChain classes, so plugging in a real key later is
a one-line config change, not a rewrite (see `docs/adr/0002-*.md`).

## Architecture

```
                        ┌──────────────┐
   POST /api/ask  ───▶  │  FastAPI     │
                        └──────┬───────┘
                               │
                       ┌───────▼────────┐
                       │  LangGraph     │
                       │  classify_intent│  (heuristic, or LLM structured output)
                       └───────┬────────┘
                     fan-out via Send API
           ┌──────────┬────────┼────────┬──────────┐
           ▼          ▼        ▼        ▼          │
        run_sql   run_mongo run_oracle run_rag      │
           │          │        │        │           │
        MySQL      MongoDB  Oracle    Qdrant         │
       (orders)   (catalog, (PL/SQL   (policy RAG)   │
                   sessions) loyalty)                │
           └──────────┴────────┴────────┴──────┐    │
                                                 ▼
                                           synthesize
                                          (LLM: mock or real)
                                                 │
                                                 ▼
                                         ChatResponse
```

Each data source is queried only when `classify_intent` decides the
question needs it -- a pure policy question never touches MySQL/Mongo/
Oracle, a pure order question never touches Qdrant. See
`docs/adr/0001-plan-then-execute-agent.md` for why the LLM only chooses
*which* tool to call, and never writes SQL/PL-SQL/Mongo queries itself.

## Why these specific databases

| Store | Data | Why |
|---|---|---|
| MySQL | `customers`, `orders`, `order_items` | Strict relational, transactional system of record |
| MongoDB | `products` (variable attributes per category), `support_sessions` (variable-length chat logs) | Naturally schema-flexible documents |
| Oracle (PL/SQL) | `customer_stats`, `customer_loyalty`, `loyalty_pkg` package | Stand-in for a legacy business-rule engine the agent must call, not reimplement |
| Qdrant | Return/shipping/FAQ policy text | Semantic retrieval over free-form prose |

Full reasoning in `docs/adr/`.

## Running it

Requires Docker and Docker Compose.

```bash
cp .env.example .env         # defaults already run in demo mode
docker compose up --build
```

This starts MySQL, MongoDB, Oracle XE, Qdrant, and the FastAPI app
together. Oracle takes the longest to become healthy on first boot
(around a minute) since it initialises a fresh database; the app's
healthcheck-gated `depends_on` waits for it.

Once it's up:

```bash
curl http://localhost:8000/api/health

curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the status of order 3?"}'

curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I return a defective headset after 60 days?"}'

curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What loyalty tier is customer 5?", "customer_id": 5}'
```

Interactive API docs: `http://localhost:8000/docs`.

## Running the app without Docker (databases elsewhere / unit tests only)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                      # graph structure, router, embeddings, mock LLM -- no live DB needed
uvicorn app.main:app --reload
```

`pytest` only exercises the pieces that don't need a live database
(`classify_intent`'s heuristic, `HashingEmbeddings`, `MockChatModel`,
and that the LangGraph graph compiles with the expected nodes). The
`/api/ask` endpoint itself needs the Docker Compose stack (or equivalent
databases reachable via `.env`) since the tool layer talks to real
MySQL/Mongo/Oracle/Qdrant connections.

## Going from demo mode to a real LLM

Edit `.env`:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
EMBEDDING_PROVIDER=openai
```

No code changes: `app/llm/provider.py` and `app/llm/embeddings.py` already
branch on these settings and return `ChatOpenAI` / `OpenAIEmbeddings`
instead of the mock classes. `classify_intent` will then use the LLM's
structured-output mode (`RouteDecision`) instead of the keyword heuristic.

## Development

Install dev dependencies (adds `pytest` and `ruff` on top of the app's own requirements):

```bash
pip install -r requirements-dev.txt
```

Run the linter and the test suite before pushing:

```bash
ruff check .
pytest -v
```

CI (`.github/workflows/ci.yml`) runs both automatically on every push and pull request against `main`.

### Production hardening

A few things beyond the happy path are worth knowing about:

- **Fault isolation** -- optional dependencies (`pymysql`, `oracledb`, `pymongo`, `qdrant_client`) are imported lazily, inside the functions that use them, not at module load time. A missing or platform-incompatible driver degrades that one data source instead of crashing the whole app at boot -- this is exactly what happened in production on Vercel and is now covered by a regression test.
- **Rate limiting** -- `/api/ask` is limited per client IP (in-memory fixed-window). This resets on cold start and isn't shared across serverless instances, which is an acceptable, documented trade-off for a demo deployment rather than a real production guarantee.
- **Global error handling** -- unhandled exceptions return a generic 500 instead of leaking a stack trace, with the real error logged server-side.
- **Input validation** -- `question` and `customer_id` are bounded (length and range) at the Pydantic model level, before they reach the graph.

See [`docs/adr/0005-production-hardening.md`](docs/adr/0005-production-hardening.md) for the full rationale and what's intentionally left out of scope (shared rate-limit storage, auth, tracing).

Licensed under [MIT](LICENSE).

## Deploying the API to Vercel (demo mode, no databases)

Vercel runs stateless serverless functions -- it cannot host the MySQL /
MongoDB / Oracle / Qdrant containers themselves. What it *can* host is the
FastAPI app in demo mode: the mock LLM and heuristic router work exactly
as they do locally, and any question that would need a live database
degrades gracefully (the tool returns "unreachable"/"error reaching..."
instead of crashing -- see `/api/health`). This is enough to demo the
API shape, the LangGraph routing, and the OpenAPI docs at `/docs` from a
public URL, without running any infrastructure.

The repo already has what Vercel needs:
- `api/index.py` -- re-exports the FastAPI `app` object; Vercel's Python
  runtime serves any ASGI `app` found under `api/*.py` automatically.
- `vercel.json` -- rewrites every request to that function.

Steps:

1. Push this project to a new GitHub repository.
2. On vercel.com, "Add New... Project", import that repository. Vercel
   auto-detects the Python runtime from `requirements.txt`; no build
   command is needed.
3. Leave the environment variables empty (or set `LLM_PROVIDER=mock`
   explicitly) -- this is what keeps it in free demo mode. Do **not** set
   `MYSQL_HOST`/`MONGO_URI`/`ORACLE_HOST`/`QDRANT_URL` to anything Vercel
   can actually reach unless you've stood up managed cloud databases
   (PlanetScale, MongoDB Atlas, Qdrant Cloud, etc.) -- that's a separate,
   larger step this deployment path does not cover.
4. Deploy. Once live, `https://<your-app>.vercel.app/docs` opens the
   interactive API docs, and `/api/health` will honestly report each
   database as unreachable, which is expected in this mode.

## Project layout

```
app/
  main.py              FastAPI app + startup RAG ingest
  config.py            All settings (env-driven), demo-mode detection
  models/schemas.py    Pydantic request/response models
  llm/provider.py      MockChatModel / ChatOpenAI / ChatAnthropic factory
  llm/embeddings.py     HashingEmbeddings / OpenAIEmbeddings factory
  db/                  MySQL / Mongo / Oracle client modules
  rag/                 Qdrant ingestion + retriever
  tools/               LangChain @tool wrappers, one per data source
  agent/               LangGraph state, router, nodes, graph definition
  api/                 FastAPI routers (chat, ingest, health)
  rate_limit.py        In-memory per-client rate limiting for /api/ask
  static/index.html    Self-contained landing page / demo chat UI
db/
  mysql/init/          Schema + seed SQL (customers, orders, order_items)
  mongo/init/          Seed script (products, support_sessions)
  oracle/init/         Schema, loyalty_pkg package, seed + batch refresh
knowledge_base/        Markdown policy docs indexed into Qdrant for RAG
docs/adr/              Architecture decision records
tests/                 Pytest suite (no live DB required)
.github/workflows/     CI (lint + tests on push/PR)
pyproject.toml         Ruff configuration
requirements-dev.txt   Dev-only deps (pytest, ruff)
LICENSE                MIT
```
