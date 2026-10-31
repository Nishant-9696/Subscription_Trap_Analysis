# Subscription Trap Analysis: Business Insights

This analysis uses synthetic data only for demonstration. The dataset contains 1,000 cleaned subscription records across 200 users and is intended to support a practical review of recurring subscription spend.

## Executive Summary

- Total monthly-equivalent subscription spend: $16466.85
- Average monthly cost per active subscription: $16.47
- Active subscriptions with low reported usage (<=2 uses/month): 218
- Users exceeding their monthly budget: 71
- High-priority subscription reviews flagged: 37

## Key Findings

1. Category spend is concentrated in fitness and education. The top category is Fitness with $4592.27 in monthly-equivalent spending, followed by Education with $3240.93.
2. 218 active subscriptions have low reported usage, which indicates a review opportunity but not automatic waste. The trigger is based on both low usage and the subscription's cost profile.
3. 71 users exceed their budget, which suggests that the budget control signal is useful when evaluating account-level subscription pressure.
4. The highest-priority subscriptions are those with a combination of high monthly-equivalent cost and low usage. This review-first list is captured in the workbook's review logic and in the SQL analysis queries.

## Top review candidates

- Unspecified Service (Fitness) for user U072 — monthly equivalent: $77.75, potential savings scenario: $46.65.
- Strava Summit (Fitness) for user U077 — monthly equivalent: $77.20, potential savings scenario: $46.32.
- Planet Fitness (Fitness) for user U030 — monthly equivalent: $72.86, potential savings scenario: $43.72.
- Nike Training Club (Fitness) for user U178 — monthly equivalent: $71.80, potential savings scenario: $43.08.
- Planet Fitness (Fitness) for user U073 — monthly equivalent: $71.40, potential savings scenario: $42.84.

## Supporting project assets

- Raw data file: subscriptions_raw.csv
- Cleaned data file: subscriptions_clean.csv
- Excel workbook: Subscription_Trap_Analysis.xlsx
- SQL scripts: 01_create_database.sql to 06_advanced_analysis.sql

The analysis is intentionally based on synthetic, non-personal data and all savings estimates are scenario-based cancellation values rather than guaranteed savings.
