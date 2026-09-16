# ADR 0004: Loyalty/risk logic lives in PL/SQL, never in Python

## Status
Accepted

## Context
Loyalty tier and risk score could be computed in Python after pulling raw
`lifetime_value` / `return_count` / `complaint_count` out of Oracle. That
would be simpler to write, but it would mean the business rule exists in
two places the moment any other system (a nightly batch job, a BI report)
also needs it -- a classic source of drift.

## Decision
`loyalty_pkg` (see `db/oracle/init/02_loyalty_pkg.sql`) is the single
owner of the tier thresholds and the risk-score formula:

- `calculate_tier` / `calculate_risk_score` are pure functions over
  `customer_stats`, callable individually.
- `refresh_loyalty` is the upsert entry point (`MERGE INTO ... USING
  (SELECT ... FROM dual)`), called whenever a customer's stats change.
- `refresh_all_loyalty` is the batch entry point (a cursor loop over
  every customer), called once at container startup by
  `03_seed_and_run.sql` to populate `customer_loyalty` from the seed
  data.

`app/db/oracle_client.py` only ever reads the pre-computed
`customer_loyalty` table, or calls `refresh_loyalty` through
`cur.callproc(...)` -- it never computes a tier or risk score in Python.

## Consequences
- Changing a tier threshold or the risk formula is a one-file PL/SQL
  change; every consumer (this agent, a future report, a nightly job)
  picks it up for free.
- The Python layer is a thin, honest client of a legacy system, which is
  the realistic shape of this kind of integration in an actual
  e-commerce company.
