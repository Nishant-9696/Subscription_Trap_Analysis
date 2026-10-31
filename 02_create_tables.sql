USE subscription_trap_db;

CREATE TABLE users (
    user_id CHAR(10) PRIMARY KEY,
    monthly_budget DECIMAL(10,2) NOT NULL,
    budget_status ENUM('within_budget', 'over_budget') NOT NULL DEFAULT 'within_budget',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscriptions (
    subscription_id VARCHAR(30) PRIMARY KEY,
    user_id CHAR(10) NOT NULL,
    subscription_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    monthly_cost DECIMAL(10,2) NOT NULL,
    billing_cycle ENUM('monthly','quarterly','annual') NOT NULL,
    start_date DATE NOT NULL,
    renewal_date DATE NOT NULL,
    monthly_usage_count INT NOT NULL DEFAULT 0,
    subscription_status ENUM('active','paused','trial','cancelled') NOT NULL,
    monthly_budget DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    monthly_equivalent_cost DECIMAL(10,2) NOT NULL,
    budget_contribution_pct DECIMAL(10,2) NOT NULL,
    review_priority ENUM('Low Priority','Medium Priority','High Priority') NOT NULL,
    potential_savings DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_subscription_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE subscription_usage (
    usage_id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_id VARCHAR(30) NOT NULL,
    usage_month DATE NOT NULL,
    monthly_usage_count INT NOT NULL,
    notes VARCHAR(255) DEFAULT NULL,
    CONSTRAINT fk_usage_subscription
        FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);
