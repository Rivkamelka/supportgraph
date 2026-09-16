# ADR 0003: Three databases, chosen by data shape, not by novelty

## Status
Accepted

## Context
The brief called for MySQL, MongoDB, and Oracle PL/SQL together. Rather
than using all three for the same kind of data (which would be an
arbitrary constraint), each was assigned the kind of data it is actually
best suited for, so the choice can be defended on its merits in an
interview.

## Decision
- **MySQL** — `customers`, `orders`, `order_items`. Strictly relational,
  transactional, foreign-keyed data with a fixed schema. This is the
  system of record for "did this purchase happen, what does it cost, what
  status is it in."
- **MongoDB** — `products` (schema varies per category: a keyboard has
  `switch_type`, a monitor has `refresh_hz`) and `support_sessions`
  (a variable-length array of chat turns per document). Both are natural
  documents, awkward as normalised relational tables.
- **Oracle (PL/SQL)** — `customer_stats` / `customer_loyalty`, fronted by
  the `loyalty_pkg` package. Plays the role of a pre-existing legacy
  system whose business rule (tier and risk-score calculation) already
  lives in a stored procedure the company depends on; the agent is a new
  consumer of that rule, not a reimplementation of it.
- **Qdrant** — the store's policy prose (returns, shipping, FAQ), because
  answering "can I return a broken headset after 60 days" needs semantic
  retrieval over free text, not a lookup.

## Consequences
- Every database in the stack has a job only it is good at, so no part of
  the project looks like it exists "because the brief asked for it."
- The agent's tool layer (`app/tools/*.py`) hides these differences
  behind a uniform `str -> str` LangChain `@tool` interface; `app/agent/nodes.py`
  never needs to know it's talking to three completely different engines.
