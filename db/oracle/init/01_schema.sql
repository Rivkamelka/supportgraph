-- Oracle plays the role of the "legacy CRM": the loyalty/risk engine this
-- company has run in PL/SQL for years, well before the AI layer existed.
-- The agent calls it exactly as any internal application would — through
-- the stored procedure interface, never by reaching into its tables.

ALTER SESSION SET CONTAINER = XEPDB1;

-- Init scripts run as SYS; without this, every object below would be
-- created in the SYS schema instead of the app's own support_app schema
-- (created automatically by the gvenzl/oracle-xe image from the
-- APP_USER/APP_USER_PASSWORD env vars), and the app's connection would
-- not see any of it.
ALTER SESSION SET CURRENT_SCHEMA = support_app;

CREATE TABLE customer_stats (
  customer_id      NUMBER        PRIMARY KEY,
  lifetime_value   NUMBER(10, 2) NOT NULL,
  return_count     NUMBER        DEFAULT 0 NOT NULL,
  complaint_count  NUMBER        DEFAULT 0 NOT NULL
);

CREATE TABLE customer_loyalty (
  customer_id      NUMBER        PRIMARY KEY,
  tier             VARCHAR2(20)  NOT NULL,
  risk_score       NUMBER(5, 2)  NOT NULL,
  last_calculated  DATE          NOT NULL,
  CONSTRAINT fk_loyalty_customer FOREIGN KEY (customer_id)
    REFERENCES customer_stats(customer_id)
);
