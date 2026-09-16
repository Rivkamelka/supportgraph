ALTER SESSION SET CONTAINER = XEPDB1;
ALTER SESSION SET CURRENT_SCHEMA = support_app;

-- LOYALTY_PKG encapsulates the business rules the support agent is not
-- allowed to reimplement: tier and risk score are computed exactly once,
-- here, so the AI layer and every other consumer see the same number.
CREATE OR REPLACE PACKAGE loyalty_pkg AS

  -- Tiers are a step function of lifetime spend. Kept as named constants
  -- rather than magic numbers so a policy change is a one-line diff.
  c_tier_platinum CONSTANT VARCHAR2(20) := 'platinum';
  c_tier_gold     CONSTANT VARCHAR2(20) := 'gold';
  c_tier_silver   CONSTANT VARCHAR2(20) := 'silver';
  c_tier_bronze   CONSTANT VARCHAR2(20) := 'bronze';

  FUNCTION calculate_tier(p_customer_id IN customer_stats.customer_id%TYPE)
    RETURN VARCHAR2;

  FUNCTION calculate_risk_score(p_customer_id IN customer_stats.customer_id%TYPE)
    RETURN NUMBER;

  PROCEDURE refresh_loyalty(p_customer_id IN customer_stats.customer_id%TYPE);

  -- Batch entry point: recomputes every customer. A nightly job would
  -- call this; the demo calls it once at container startup to populate
  -- customer_loyalty from the seeded customer_stats rows.
  PROCEDURE refresh_all_loyalty;

END loyalty_pkg;
/

CREATE OR REPLACE PACKAGE BODY loyalty_pkg AS

  FUNCTION calculate_tier(p_customer_id IN customer_stats.customer_id%TYPE)
    RETURN VARCHAR2
  IS
    v_ltv customer_stats.lifetime_value%TYPE;
  BEGIN
    SELECT lifetime_value INTO v_ltv
    FROM customer_stats
    WHERE customer_id = p_customer_id;

    IF v_ltv >= 1000 THEN
      RETURN c_tier_platinum;
    ELSIF v_ltv >= 500 THEN
      RETURN c_tier_gold;
    ELSIF v_ltv >= 150 THEN
      RETURN c_tier_silver;
    ELSE
      RETURN c_tier_bronze;
    END IF;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20010, 'No customer_stats row for customer_id ' || p_customer_id);
  END calculate_tier;

  -- Risk is a simple weighted formula on returns and complaints relative
  -- to how much the customer has actually bought, clamped to [0, 100].
  -- A real engine would weight recency too; the demo keeps the rule
  -- readable so it is easy to defend in an interview.
  FUNCTION calculate_risk_score(p_customer_id IN customer_stats.customer_id%TYPE)
    RETURN NUMBER
  IS
    v_ltv       customer_stats.lifetime_value%TYPE;
    v_returns   customer_stats.return_count%TYPE;
    v_complaints customer_stats.complaint_count%TYPE;
    v_raw       NUMBER;
  BEGIN
    SELECT lifetime_value, return_count, complaint_count
    INTO v_ltv, v_returns, v_complaints
    FROM customer_stats
    WHERE customer_id = p_customer_id;

    v_raw := (v_returns * 12) + (v_complaints * 18) - (LOG(10, GREATEST(v_ltv, 1)) * 5);
    RETURN GREATEST(0, LEAST(100, ROUND(v_raw, 2)));
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RAISE_APPLICATION_ERROR(-20010, 'No customer_stats row for customer_id ' || p_customer_id);
  END calculate_risk_score;

  PROCEDURE refresh_loyalty(p_customer_id IN customer_stats.customer_id%TYPE)
  IS
    v_tier VARCHAR2(20);
    v_risk NUMBER;
  BEGIN
    v_tier := calculate_tier(p_customer_id);
    v_risk := calculate_risk_score(p_customer_id);

    MERGE INTO customer_loyalty tgt
    USING (SELECT p_customer_id AS customer_id FROM dual) src
    ON (tgt.customer_id = src.customer_id)
    WHEN MATCHED THEN
      UPDATE SET tier = v_tier, risk_score = v_risk, last_calculated = SYSDATE
    WHEN NOT MATCHED THEN
      INSERT (customer_id, tier, risk_score, last_calculated)
      VALUES (p_customer_id, v_tier, v_risk, SYSDATE);

    COMMIT;
  END refresh_loyalty;

  PROCEDURE refresh_all_loyalty
  IS
    CURSOR c_customers IS SELECT customer_id FROM customer_stats;
  BEGIN
    FOR r IN c_customers LOOP
      refresh_loyalty(r.customer_id);
    END LOOP;
  END refresh_all_loyalty;

END loyalty_pkg;
/
