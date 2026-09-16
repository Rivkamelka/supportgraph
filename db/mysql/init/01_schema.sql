-- MySQL schema: transactional data (customers, orders, order items).
-- This is the "system of record" for purchases; MongoDB holds the catalog
-- and unstructured session data, Oracle holds the legacy loyalty engine.

CREATE TABLE IF NOT EXISTS customers (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  first_name      VARCHAR(80)  NOT NULL,
  last_name       VARCHAR(80)  NOT NULL,
  email           VARCHAR(160) NOT NULL UNIQUE,
  country         VARCHAR(2)   NOT NULL,
  signup_date     DATE         NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  customer_id     INT NOT NULL,
  order_date      DATE NOT NULL,
  status          ENUM('placed', 'shipped', 'delivered', 'returned', 'cancelled') NOT NULL DEFAULT 'placed',
  total_amount    DECIMAL(10, 2) NOT NULL,
  CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS order_items (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  order_id        INT NOT NULL,
  product_sku     VARCHAR(32) NOT NULL,
  quantity        INT NOT NULL,
  unit_price      DECIMAL(10, 2) NOT NULL,
  CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_sku ON order_items(product_sku);
