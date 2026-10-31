USE subscription_trap_db;

SET FOREIGN_KEY_CHECKS = 0;

LOAD DATA INFILE 'C:/Data Analytics/subscriptions_clean.csv'
INTO TABLE subscriptions
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
    user_id = @user_id,
    subscription_id = @subscription_id,
    subscription_name = @subscription_name,
    category = @category,
    monthly_cost = @monthly_cost,
    billing_cycle = LOWER(@billing_cycle),
    start_date = STR_TO_DATE(@start_date, '%Y-%m-%d'),
    renewal_date = STR_TO_DATE(@renewal_date, '%Y-%m-%d'),
    monthly_usage_count = @monthly_usage_count,
    subscription_status = LOWER(@subscription_status),
    monthly_budget = @monthly_budget,
    payment_method = @payment_method,
    monthly_equivalent_cost = @monthly_equivalent_cost,
    budget_contribution_pct = @budget_contribution_pct,
    review_priority = @review_priority,
    potential_savings = @potential_savings;

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO users (user_id, monthly_budget, budget_status)
SELECT DISTINCT user_id, monthly_budget,
    CASE
        WHEN monthly_budget >= (SELECT SUM(monthly_equivalent_cost) FROM subscriptions s2 WHERE s2.user_id = s1.user_id)
        THEN 'within_budget'
        ELSE 'over_budget'
    END AS budget_status
FROM subscriptions s1
ON DUPLICATE KEY UPDATE
    monthly_budget = VALUES(monthly_budget),
    budget_status = VALUES(budget_status);

INSERT INTO subscription_usage (subscription_id, usage_month, monthly_usage_count, notes)
SELECT
    subscription_id,
    DATE_FORMAT(start_date, '%Y-%m-01') AS usage_month,
    monthly_usage_count,
    CONCAT('Synthetic usage record for ', subscription_name)
FROM subscriptions;
