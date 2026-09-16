# ADR 0001: Plan-then-execute, not a free-roaming tool agent

## Status
Accepted

## Context
LangGraph and LangChain make it easy to build a ReAct-style agent that
lets the LLM decide, turn by turn, which tool to call and with what raw
input (including writing its own SQL). That is flexible, but it means an
LLM's output can end up executing directly against MySQL, Oracle or
MongoDB with no static checking in between -- and in "demo mode" (no API
key), there is no LLM reasoning loop to drive that decision at all.

## Decision
The graph is a **plan-then-execute** pipeline, not a free-roaming agent:

1. `classify_intent` decides *which* data sources are relevant (sql /
   mongo / oracle / rag) -- either a keyword heuristic (demo mode) or a
   structured-output LLM call (real key). It never produces raw SQL,
   PL/SQL, or Mongo queries.
2. Each `run_*` node calls exactly one pre-written, parameterised tool
   function (`app/tools/*.py`). The tool owns the query; the LLM only
   supplies the natural-language question and, when present, a customer
   id extracted with a regex.
3. `synthesize` is the only node that touches an LLM to produce prose,
   and it is only allowed to phrase the tool findings it is given -- the
   prompt explicitly says to answer only from the findings block.

## Consequences
- No SQL/PL-SQL injection surface from LLM output, because the LLM never
  writes a query.
- Demo mode (no API key) and real-LLM mode share the exact same graph and
  the exact same tool layer; only `classify_intent`'s decision-making and
  `synthesize`'s phrasing change.
- The tradeoff: the agent cannot answer an arbitrary ad-hoc question that
  doesn't map to one of the four wired tools. That's an accepted
  limitation for a support-domain agent, not a general-purpose SQL bot.

This mirrors the same decision made in the Insight project (deterministic
`executeSpec` never contains model-authored code, only a validated
`AnalysisSpec`).
