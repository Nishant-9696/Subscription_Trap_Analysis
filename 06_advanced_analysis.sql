USE subscription_trap_db;

-- 9. How does subscription spending vary by billing cycle?
SELECT billing_cycle,
       COUNT(*) AS subscription_count,
       ROUND(SUM(monthly_equivalent_cost), 2) AS total_spend,
       ROUND(AVG(monthly_equivalent_cost), 2) AS avg_spend_per_subscription
FROM subscriptions
GROUP BY billing_cycle
ORDER BY total_spend DESC;

-- 10. What is the potential monthly saving if selected subscriptions are cancelled?
SELECT subscription_name,
       user_id,
       monthly_equivalent_cost,
       potential_savings,
       CASE
           WHEN review_priority = 'High Priority' THEN 'High-risk cancellation scenario'
           WHEN review_priority = 'Medium Priority' THEN 'Moderate review scenario'
           ELSE 'Low-impact scenario'
       END AS cancellation_scenario
FROM subscriptions
WHERE review_priority IN ('High Priority', 'Medium Priority')
ORDER BY potential_savings DESC;

-- 11. Which users have the highest number of active subscriptions?
SELECT u.user_id,
       COUNT(s.subscription_id) AS active_subscription_count
FROM users u
LEFT JOIN subscriptions s
    ON s.user_id = u.user_id
   AND s.subscription_status = 'active'
GROUP BY u.user_id
ORDER BY active_subscription_count DESC, u.user_id
LIMIT 10;

-- 12. Which categories have the highest proportion of underused subscriptions?
WITH category_totals AS (
    SELECT category,
           COUNT(*) AS total_subscriptions
    FROM subscriptions
    GROUP BY category
),
category_underused AS (
    SELECT category,
           COUNT(*) AS underused_subscriptions
    FROM subscriptions
    WHERE monthly_usage_count <= 2
    GROUP BY category
)
SELECT c.category,
       c.total_subscriptions,
       u.underused_subscriptions,
       ROUND((u.underused_subscriptions / c.total_subscriptions) * 100, 2) AS pct_underused
FROM category_totals c
JOIN category_underused u ON u.category = c.category
ORDER BY pct_underused DESC;

-- 13. How does spending differ between subscription categories?
SELECT category,
       ROUND(SUM(monthly_equivalent_cost), 2) AS total_spend,
       ROUND(AVG(monthly_equivalent_cost), 2) AS avg_spend,
       ROUND((SUM(monthly_equivalent_cost) / (SELECT SUM(monthly_equivalent_cost) FROM subscriptions)) * 100, 2) AS pct_of_total
FROM subscriptions
GROUP BY category
ORDER BY total_spend DESC;

-- 14. Which expensive subscriptions have relatively low usage?
SELECT subscription_name,
       category,
       monthly_equivalent_cost,
       monthly_usage_count,
       ROUND((monthly_equivalent_cost / NULLIF(monthly_usage_count, 0)), 2) AS cost_per_use
FROM subscriptions
WHERE monthly_equivalent_cost >= 25
  AND monthly_usage_count <= 5
ORDER BY cost_per_use DESC;

-- 15. Which subscriptions should users review first?
WITH review_scores AS (
    SELECT subscription_id,
           subscription_name,
           user_id,
           category,
           monthly_equivalent_cost,
           monthly_usage_count,
           review_priority,
           potential_savings,
           ROW_NUMBER() OVER (
               ORDER BY potential_savings DESC, monthly_equivalent_cost DESC
           ) AS review_rank
    FROM subscriptions
)
SELECT subscription_name,
       user_id,
       category,
       monthly_equivalent_cost,
       monthly_usage_count,
       review_priority,
       potential_savings,
       review_rank
FROM review_scores
WHERE review_rank <= 25
ORDER BY review_rank ASC;

-- 16. Which users have the strongest budget pressure combined with high review priority?
SELECT s.user_id,
       SUM(s.monthly_equivalent_cost) AS total_spend,
       COUNT(CASE WHEN s.review_priority = 'High Priority' THEN 1 END) AS high_priority_count,
       ROUND((SUM(s.monthly_equivalent_cost) / NULLIF(u.monthly_budget, 0)) * 100, 2) AS budget_pressure_pct
FROM subscriptions s
JOIN users u ON u.user_id = s.user_id
GROUP BY s.user_id, u.monthly_budget
HAVING high_priority_count > 0
ORDER BY budget_pressure_pct DESC, high_priority_count DESC;
