-- E-Commerce Hackathon: 5 business queries (SQLite)
-- Net revenue = quantity * price * (1 - discount), valid and non-returned orders only

-- Query 1: Total net revenue
WITH sales AS (
    SELECT o.order_id, o.customer_id, o.product_id,
           date(o.order_date) AS order_date,
           o.quantity,
           CASE WHEN o.unit_price > 0 THEN o.unit_price ELSE p.unit_price END AS price,
           o.discount
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    WHERE date(o.order_date) IS NOT NULL
      AND o.quantity > 0
      AND o.returned = 0
)

SELECT ROUND(SUM(quantity * price * (1 - discount)), 2) AS total_net_revenue,
       COUNT(*) AS total_orders
FROM sales;

-- Query 2: Top 10 customers by spending
WITH sales AS (
    SELECT o.order_id, o.customer_id, o.product_id,
           date(o.order_date) AS order_date,
           o.quantity,
           CASE WHEN o.unit_price > 0 THEN o.unit_price ELSE p.unit_price END AS price,
           o.discount
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    WHERE date(o.order_date) IS NOT NULL
      AND o.quantity > 0
      AND o.returned = 0
)

SELECT c.customer_name,
       upper(substr(trim(c.city), 1, 1)) || lower(substr(trim(c.city), 2)) AS city,
       COUNT(*) AS number_of_orders,
       ROUND(SUM(s.quantity * s.price * (1 - s.discount)), 2) AS total_spending
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY total_spending DESC
LIMIT 10;

-- Query 3: Category-wise revenue, order count and quantity sold
WITH sales AS (
    SELECT o.order_id, o.customer_id, o.product_id,
           date(o.order_date) AS order_date,
           o.quantity,
           CASE WHEN o.unit_price > 0 THEN o.unit_price ELSE p.unit_price END AS price,
           o.discount
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    WHERE date(o.order_date) IS NOT NULL
      AND o.quantity > 0
      AND o.returned = 0
)

SELECT lower(trim(p.category)) AS category,
       ROUND(SUM(s.quantity * s.price * (1 - s.discount)), 2) AS net_revenue,
       COUNT(*) AS order_count,
       SUM(s.quantity) AS quantity_sold
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY lower(trim(p.category))
ORDER BY net_revenue DESC;

-- Query 4: Monthly net revenue trend
WITH sales AS (
    SELECT o.order_id, o.customer_id, o.product_id,
           date(o.order_date) AS order_date,
           o.quantity,
           CASE WHEN o.unit_price > 0 THEN o.unit_price ELSE p.unit_price END AS price,
           o.discount
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    WHERE date(o.order_date) IS NOT NULL
      AND o.quantity > 0
      AND o.returned = 0
)

SELECT strftime('%Y-%m', order_date) AS month,
       ROUND(SUM(quantity * price * (1 - discount)), 2) AS net_revenue
FROM sales
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month;

-- Query 5: Top 5 products by net revenue
WITH sales AS (
    SELECT o.order_id, o.customer_id, o.product_id,
           date(o.order_date) AS order_date,
           o.quantity,
           CASE WHEN o.unit_price > 0 THEN o.unit_price ELSE p.unit_price END AS price,
           o.discount
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    WHERE date(o.order_date) IS NOT NULL
      AND o.quantity > 0
      AND o.returned = 0
)

SELECT p.product_name,
       lower(trim(p.category)) AS category,
       ROUND(SUM(s.quantity * s.price * (1 - s.discount)), 2) AS net_revenue
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.product_id
ORDER BY net_revenue DESC
LIMIT 5;

