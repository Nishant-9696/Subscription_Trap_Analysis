USE subscription_trap_db;

CREATE TABLE subscription_staging LIKE subscriptions;

SET FOREIGN_KEY_CHECKS = 0;

LOAD DATA INFILE 'C:/Data Analytics/subscriptions_raw.csv'
INTO TABLE subscription_staging
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    @user_id,
    @subscription_id,
    @subscription_name,
    @category,
    @monthly_cost,
    @billing_cycle,
    @start_date,
    @renewal_date,
    @monthly_usage_count,
    @subscription_status,
    @monthly_budget,
    @payment_method,
    @monthly_equivalent_cost,
    @budget_contribution_pct,
    @review_priority,
    @potential_savings
)
SET
    user_id = TRIM(@user_id),
    subscription_id = TRIM(@subscription_id),
    subscription_name = COALESCE(NULLIF(TRIM(@subscription_name), ''), 'Unspecified Service'),
    category = COALESCE(NULLIF(TRIM(@category), ''), 'Other'),
    monthly_cost = CASE WHEN TRY_CAST(@monthly_cost AS DECIMAL(10,2)) IS NULL THEN 0 ELSE ABS(TRY_CAST(@monthly_cost AS DECIMAL(10,2))) END,
    billing_cycle = CASE
        WHEN LOWER(TRIM(@billing_cycle)) IN ('yearly','year') THEN 'annual'
        WHEN LOWER(TRIM(@billing_cycle)) IN ('quarter','quarterly') THEN 'quarterly'
        ELSE 'monthly'
    END,
    start_date = CASE WHEN STR_TO_DATE(@start_date, '%Y-%m-%d') IS NULL THEN DATE '2024-01-01' ELSE STR_TO_DATE(@start_date, '%Y-%m-%d') END,
    renewal_date = CASE WHEN STR_TO_DATE(@renewal_date, '%Y-%m-%d') IS NULL THEN DATE '2025-01-01' ELSE STR_TO_DATE(@renewal_date, '%Y-%m-%d') END,
    monthly_usage_count = CASE WHEN TRY_CAST(@monthly_usage_count AS SIGNED) IS NULL THEN 0 ELSE ABS(TRY_CAST(@monthly_usage_count AS SIGNED)) END,
    subscription_status = CASE
        WHEN LOWER(TRIM(@subscription_status)) IN ('active','current','enabled') THEN 'active'
        WHEN LOWER(TRIM(@subscription_status)) IN ('paused','suspended') THEN 'paused'
        WHEN LOWER(TRIM(@subscription_status)) IN ('trial','free trial') THEN 'trial'
        WHEN LOWER(TRIM(@subscription_status)) IN ('cancelled','canceled','inactive') THEN 'cancelled'
        ELSE 'active'
    END,
    monthly_budget = CASE WHEN TRY_CAST(@monthly_budget AS DECIMAL(10,2)) IS NULL OR TRY_CAST(@monthly_budget AS DECIMAL(10,2)) <= 0 THEN 60.00 ELSE TRY_CAST(@monthly_budget AS DECIMAL(10,2)) END,
    payment_method = COALESCE(NULLIF(TRIM(@payment_method), ''), 'Credit Card');

DELETE FROM subscription_staging
WHERE user_id = '' OR subscription_id = '' OR subscription_name = '' OR monthly_cost <= 0;

INSERT INTO users (user_id, monthly_budget, budget_status)
SELECT DISTINCT user_id, monthly_budget,
    CASE WHEN monthly_budget >= (SELECT SUM(monthly_equivalent_cost) FROM subscription_staging s2 WHERE s2.user_id = s1.user_id) THEN 'within_budget' ELSE 'over_budget' END
FROM subscription_staging s1
ON DUPLICATE KEY UPDATE monthly_budget = VALUES(monthly_budget), budget_status = VALUES(budget_status);

INSERT INTO subscriptions (
    subscription_id, user_id, subscription_name, category, monthly_cost, billing_cycle,
    start_date, renewal_date, monthly_usage_count, subscription_status, monthly_budget,
    payment_method, monthly_equivalent_cost, budget_contribution_pct, review_priority, potential_savings
)
SELECT
    subscription_id,
    user_id,
    subscription_name,
    category,
    monthly_cost,
    billing_cycle,
    start_date,
    renewal_date,
    monthly_usage_count,
    subscription_status,
    monthly_budget,
    payment_method,
    CASE
        WHEN billing_cycle = 'quarterly' THEN ROUND(monthly_cost / 3, 2)
        WHEN billing_cycle = 'annual' THEN ROUND(monthly_cost / 12, 2)
        ELSE ROUND(monthly_cost, 2)
    END,
    ROUND((CASE
        WHEN billing_cycle = 'quarterly' THEN ROUND(monthly_cost / 3, 2)
        WHEN billing_cycle = 'annual' THEN ROUND(monthly_cost / 12, 2)
        ELSE ROUND(monthly_cost, 2)
    END / monthly_budget) * 100, 2),
    CASE
        WHEN (CASE
            WHEN billing_cycle = 'quarterly' THEN ROUND(monthly_cost / 3, 2)
            WHEN billing_cycle = 'annual' THEN ROUND(monthly_cost / 12, 2)
            ELSE ROUND(monthly_cost, 2)
        END >= 32 AND monthly_usage_count <= 2) THEN 'High Priority'
        WHEN (CASE
            WHEN billing_cycle = 'quarterly' THEN ROUND(monthly_cost / 3, 2)
            WHEN billing_cycle = 'annual' THEN ROUND(monthly_cost / 12, 2)
            ELSE ROUND(monthly_cost, 2)
        END >= 20 AND monthly_usage_count <= 5) THEN 'Medium Priority'
        ELSE 'Low Priority'
    END,
    CASE
        WHEN (CASE
            WHEN billing_cycle = 'quarterly' THEN ROUND(monthly_cost / 3, 2)
            WHEN billing_cycle = 'annual' THEN ROUND(monthly_cost / 12, 2)
            ELSE ROUND(monthly_cost, 2)
        END >= 32 AND monthly_usage_count <= 2) THEN ROUND((CASE
            WHEN billing_cycle = 'quarterly' THEN ROUND(monthly_cost / 3, 2)
            WHEN billing_cycle = 'annual' THEN ROUND(monthly_cost / 12, 2)
            ELSE ROUND(monthly_cost, 2)
        END * 0.60), 2)
        ELSE ROUND((CASE
            WHEN billing_cycle = 'quarterly' THEN ROUND(monthly_cost / 3, 2)
            WHEN billing_cycle = 'annual' THEN ROUND(monthly_cost / 12, 2)
            ELSE ROUND(monthly_cost, 2)
        END * 0.25), 2)
    END
FROM subscription_staging
ON DUPLICATE KEY UPDATE
    monthly_cost = VALUES(monthly_cost),
    monthly_equivalent_cost = VALUES(monthly_equivalent_cost),
    review_priority = VALUES(review_priority),
    potential_savings = VALUES(potential_savings);

INSERT INTO subscription_usage (subscription_id, usage_month, monthly_usage_count, notes)
SELECT
    subscription_id,
    DATE_FORMAT(start_date, '%Y-%m-01'),
    monthly_usage_count,
    CONCAT('Synthetic record from cleaned staging for ', subscription_name)
FROM subscriptions;

SET FOREIGN_KEY_CHECKS = 1;
