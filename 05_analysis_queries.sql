USE subscription_trap_db;

-- 1. Which subscription categories cost the most?
SELECT category,
       ROUND(SUM(monthly_equivalent_cost), 2) AS total_category_spend
FROM subscriptions
GROUP BY category
ORDER BY total_category_spend DESC;

-- 2. Which subscriptions have high costs but low usage?
SELECT subscription_name,
       category,
       monthly_equivalent_cost,
       monthly_usage_count
FROM subscriptions
WHERE monthly_usage_count <= 2
  AND monthly_equivalent_cost >= 20
ORDER BY monthly_equivalent_cost DESC;

-- 3. Which users spend the most on subscriptions?
SELECT u.user_id,
       u.monthly_budget,
       ROUND(SUM(s.monthly_equivalent_cost), 2) AS total_spend
FROM users u
JOIN subscriptions s ON s.user_id = u.user_id
GROUP BY u.user_id, u.monthly_budget
ORDER BY total_spend DESC
LIMIT 10;

-- 4. Which users exceed their monthly budgets?
SELECT u.user_id,
       u.monthly_budget,
       ROUND(SUM(s.monthly_equivalent_cost), 2) AS current_spend,
       ROUND(SUM(s.monthly_equivalent_cost) - u.monthly_budget, 2) AS over_budget_amount
FROM users u
JOIN subscriptions s ON s.user_id = u.user_id
GROUP BY u.user_id, u.monthly_budget
HAVING current_spend > u.monthly_budget
ORDER BY over_budget_amount DESC;

-- 5. Which subscriptions have upcoming renewals?
SELECT subscription_name,
       user_id,
       renewal_date,
       monthly_equivalent_cost
FROM subscriptions
WHERE renewal_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
ORDER BY renewal_date ASC;

-- 6. What is the average subscription cost?
SELECT ROUND(AVG(monthly_equivalent_cost), 2) AS avg_subscription_cost
FROM subscriptions;

-- 7. Which categories have the highest average cost?
SELECT category,
       ROUND(AVG(monthly_equivalent_cost), 2) AS avg_category_cost,
       COUNT(*) AS subscription_count
FROM subscriptions
GROUP BY category
ORDER BY avg_category_cost DESC;

-- 8. Which subscriptions have not been used recently, if usage history is available?
SELECT s.subscription_name,
       s.user_id,
       MAX(u.usage_month) AS last_usage_month,
       s.monthly_usage_count
FROM subscriptions s
LEFT JOIN subscription_usage u ON u.subscription_id = s.subscription_id
GROUP BY s.subscription_id, s.subscription_name, s.user_id, s.monthly_usage_count
HAVING MAX(u.usage_month) IS NULL
    OR MAX(u.usage_month) < DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
ORDER BY last_usage_month ASC;
