# ADR 0005: Production hardening after the first live deploy

## Status
Accepted

## Context
The first deployment to Vercel surfaced three real bugs that only show up
once code runs on someone else's infrastructure instead of a local
machine: a heavy, eagerly-imported dependency (`qdrant-client` /
`langchain-qdrant`) that behaved differently in Vercel's Python sandbox;
Vercel auto-detecting the committed `.env.example` and creating real
environment variables with an *empty string* value, which pydantic
rejected as an invalid `int`; and a routing config (`vercel.json`
`rewrites`) that doesn't correctly forward the original request path to a
Python ASGI function, the way the older `builds`/`routes` config does.

Each of those was fixed reactively, one deploy at a time. This ADR is the
follow-up pass: turning "it works now" into "it's hard to break again,"
and adding the pieces a demo skips but a production service doesn't.

## Decisions

**Lazy imports for every optional data-source client** (`app/db/*.py`,
`app/rag/ingest.py`, `app/rag/retriever.py`). A driver that fails to
import now only breaks the one call that needed it -- caught by the same
try/except every tool already uses -- instead of crashing the entire app
before it can serve a single request. This is a general hardening, not a
one-off fix: it protects against the *next* dependency that has trouble
with the code online — not just the one already found.

**A model-level validator on `Settings`** (`app/config.py`) that treats
an empty-string environment variable as "not set" and falls back to the
field's default, for every field, not just the `int` ones. Covered by a
regression test (`tests/test_config.py`) that reproduces the exact crash.

**A best-effort, in-memory rate limiter** (`app/rate_limit.py`) on
`/api/ask`: 20 requests per 60 seconds per client IP (from
`X-Forwarded-For`, since Vercel sits in front as a proxy). Explicitly
documented as per-instance, not global — a serverless cold start resets
it, and a shared store (Redis / Upstash) would be the real fix for actual
production traffic. Shipping the honest, limited version now and naming
its limit is preferred over shipping nothing, or overselling what it
does.

**A global exception handler** (`app/main.py`) so any bug that isn't
already caught by a route returns a generic `{"detail": "Internal server
error"}` instead of leaking a stack trace (file paths, query shapes) to
the client, while still logging the full traceback server-side.

**CI on every push** (`.github/workflows/ci.yml`): installs
`requirements-dev.txt`, runs `ruff check` and the full `pytest` suite.
Catches the kind of regression a manual "looks fine locally" check
misses, and is the same discipline the sibling Insight project already
has.

**Expanded test coverage**: the original suite only covered the
heuristic router, the hashing embeddings and the mock LLM -- none of it
touched the actual tool layer. `tests/test_sql_tool.py`,
`test_mongo_tool.py`, `test_oracle_tool.py` and `test_rag_tool.py` mock
each data-source client and assert on the tool's formatting and its
error-message path; `tests/test_api.py` exercises the full FastAPI app
through `TestClient`, including the new rate limiter and the request
validation added to `ChatRequest` (`max_length` on the question,
`ge=1` on `customer_id`).

## Consequences
- A dependency issue, a bad config value, or an unhandled exception each
  degrade to a clear, bounded failure instead of taking down the whole
  service -- exactly the reliability bar a support-facing tool needs.
- The project now has a visible, automated signal (CI) that a change
  didn't break anything, rather than relying on manually re-running
  `pytest` before every push.
- What's still explicitly out of scope, and named as such rather than
  quietly skipped: a shared rate-limit store, authentication/authorization
  on the API, and structured request tracing/observability. Those are the
  right next three steps for turning this from "solid demo" into
  "production service," not gaps the project pretends don't exist.
