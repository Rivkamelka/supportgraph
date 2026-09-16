ALTER SESSION SET CONTAINER = XEPDB1;
ALTER SESSION SET CURRENT_SCHEMA = support_app;

-- customer_id values mirror the MySQL customers table (1-6) so the agent
-- can join a MySQL identity to an Oracle loyalty tier in one answer.
INSERT INTO customer_stats (customer_id, lifetime_value, return_count, complaint_count) VALUES (1, 438.40, 1, 0);
INSERT INTO customer_stats (customer_id, lifetime_value, return_count, complaint_count) VALUES (2, 429.00, 0, 0);
INSERT INTO customer_stats (customer_id, lifetime_value, return_count, complaint_count) VALUES (3, 240.50, 1, 1);
INSERT INTO customer_stats (customer_id, lifetime_value, return_count, complaint_count) VALUES (4, 64.99,  0, 0);
INSERT INTO customer_stats (customer_id, lifetime_value, return_count, complaint_count) VALUES (5, 993.00, 1, 2);
INSERT INTO customer_stats (customer_id, lifetime_value, return_count, complaint_count) VALUES (6, 39.90,  0, 0);
COMMIT;

BEGIN
  loyalty_pkg.refresh_all_loyalty;
END;
/
