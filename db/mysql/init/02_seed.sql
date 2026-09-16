-- Demo data: 6 customers, a spread of order statuses and dates so that
-- SQL aggregation questions ("how many orders did customer X return?")
-- have a real, checkable answer.

INSERT INTO customers (first_name, last_name, email, country, signup_date) VALUES
  ('Rivka',   'Levy',     'rivka.levy@example.com',    'FR', '2024-02-11'),
  ('Noa',     'Cohen',    'noa.cohen@example.com',     'IL', '2023-08-03'),
  ('Marc',    'Dupont',   'marc.dupont@example.com',   'FR', '2022-11-19'),
  ('Sarah',   'Klein',    'sarah.klein@example.com',   'US', '2024-06-27'),
  ('Ilan',    'Ben David','ilan.bendavid@example.com', 'IL', '2021-05-02'),
  ('Julie',   'Moreau',   'julie.moreau@example.com',  'FR', '2025-01-15');

INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES
  (1, '2025-03-02', 'delivered', 129.90),
  (1, '2025-05-18', 'returned',  59.00),
  (1, '2025-08-30', 'delivered', 249.50),
  (2, '2024-12-01', 'delivered', 89.00),
  (2, '2025-04-22', 'delivered', 340.00),
  (3, '2023-01-10', 'delivered', 45.00),
  (3, '2023-06-14', 'cancelled', 199.00),
  (3, '2024-09-05', 'delivered', 76.50),
  (3, '2025-02-27', 'returned',  120.00),
  (4, '2025-07-01', 'shipped',   64.99),
  (5, '2022-03-11', 'delivered', 510.00),
  (5, '2023-10-08', 'returned',  95.00),
  (5, '2024-05-19', 'delivered', 210.00),
  (5, '2025-06-30', 'delivered', 178.00),
  (6, '2025-09-01', 'placed',    39.90);

INSERT INTO order_items (order_id, product_sku, quantity, unit_price) VALUES
  (1,  'KEY-100', 1, 79.00), (1,  'MOU-200', 1, 45.00),
  (2,  'CAB-050', 2, 29.50),
  (3,  'MON-270', 1, 249.50),
  (4,  'HDS-300', 1, 89.00),
  (5,  'DSK-STND', 1, 340.00),
  (6,  'MAT-010', 1, 19.00), (6, 'CAB-050', 1, 26.00),
  (7,  'MON-270', 1, 199.00),
  (8,  'MIC-400', 1, 76.50),
  (9,  'HDS-300', 1, 120.00),
  (10, 'SPK-500', 1, 64.99),
  (11, 'DSK-STND', 1, 340.00), (11, 'KEY-100', 2, 85.00),
  (12, 'MON-270', 1, 95.00),
  (13, 'HDS-300', 1, 129.00), (13, 'MIC-400', 1, 81.00),
  (14, 'SPK-500', 2, 89.00),
  (15, 'MAT-010', 1, 19.90), (15, 'CAB-050', 1, 20.00);
