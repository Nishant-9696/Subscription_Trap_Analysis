from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "subscriptions_clean.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    for date_col in ["start_date", "renewal_date"]:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    numeric_cols = [
        "monthly_cost",
        "monthly_usage_count",
        "monthly_budget",
        "monthly_equivalent_cost",
        "budget_contribution_pct",
        "potential_savings",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["review_priority"] = df["review_priority"].fillna("Low Priority")
    df["subscription_status"] = df["subscription_status"].fillna("active")
    return df


df = load_data()

st.set_page_config(
    page_title="Subscription Trap Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Subscription Trap Analysis Dashboard")
st.caption("Interactive dashboard built from the project subscription data and Tableau-ready metrics.")

with st.sidebar:
    st.header("Filters")
    categories = st.multiselect(
        "Category",
        options=sorted(df["category"].dropna().unique()),
        default=sorted(df["category"].dropna().unique()),
    )
    statuses = st.multiselect(
        "Subscription status",
        options=sorted(df["subscription_status"].dropna().unique()),
        default=sorted(df["subscription_status"].dropna().unique()),
    )
    priorities = st.multiselect(
        "Review priority",
        options=sorted(df["review_priority"].dropna().unique()),
        default=sorted(df["review_priority"].dropna().unique()),
    )
    billing_cycles = st.multiselect(
        "Billing cycle",
        options=sorted(df["billing_cycle"].dropna().unique()),
        default=sorted(df["billing_cycle"].dropna().unique()),
    )

    min_usage = st.slider(
        "Minimum monthly usage",
        min_value=int(df["monthly_usage_count"].min()),
        max_value=int(df["monthly_usage_count"].max()),
        value=int(df["monthly_usage_count"].min()),
    )
    min_cost = st.slider(
        "Minimum monthly equivalent cost",
        min_value=0,
        max_value=int(df["monthly_equivalent_cost"].max()),
        value=0,
    )

filtered = df[
    df["category"].isin(categories)
    & df["subscription_status"].isin(statuses)
    & df["review_priority"].isin(priorities)
    & df["billing_cycle"].isin(billing_cycles)
    & (df["monthly_usage_count"] >= min_usage)
    & (df["monthly_equivalent_cost"] >= min_cost)
].copy()

if filtered.empty:
    st.warning("No subscriptions match the selected filters. Try widening the filter values.")
    st.stop()

user_budget_pressure = (
    filtered.groupby("user_id", as_index=False)
    .agg(total_spend=("monthly_equivalent_cost", "sum"), monthly_budget=("monthly_budget", "first"))
    .assign(budget_gap=lambda x: x["total_spend"] - x["monthly_budget"])
    .sort_values("total_spend", ascending=False)
)

budget_overrun_users = int((user_budget_pressure["total_spend"] > user_budget_pressure["monthly_budget"]).sum())
low_usage_count = int((filtered["monthly_usage_count"] <= 2).sum())
review_candidates = int((filtered["review_priority"] == "High Priority").sum())

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("Total spend", f"${filtered['monthly_equivalent_cost'].sum():,.2f}")
with kpi2:
    st.metric("Avg. monthly cost", f"${filtered['monthly_equivalent_cost'].mean():,.2f}")
with kpi3:
    st.metric("Low-usage subs", low_usage_count)
with kpi4:
    st.metric("Users over budget", budget_overrun_users)
with kpi5:
    st.metric("High-priority reviews", review_candidates)

st.markdown("---")

left_col, right_col = st.columns(2)
with left_col:
    category_spend = (
        filtered.groupby("category", as_index=False)["monthly_equivalent_cost"]
        .sum()
        .sort_values("monthly_equivalent_cost", ascending=False)
    )
    fig_category = px.bar(
        category_spend,
        x="category",
        y="monthly_equivalent_cost",
        color="category",
        title="Monthly spend by category",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_category.update_layout(xaxis_title="Category", yaxis_title="Cost ($)", template="plotly_white")
    st.plotly_chart(fig_category, use_container_width=True)

with right_col:
    top_users = user_budget_pressure.head(10)
    fig_users = px.bar(
        top_users,
        x="user_id",
        y="total_spend",
        color="total_spend",
        title="Top 10 users by subscription spend",
        color_continuous_scale="Viridis",
    )
    fig_users.update_layout(xaxis_title="User ID", yaxis_title="Spend ($)", template="plotly_white")
    st.plotly_chart(fig_users, use_container_width=True)

left_col, right_col = st.columns(2)
with left_col:
    scatter = filtered[["user_id", "category", "monthly_equivalent_cost", "monthly_usage_count", "review_priority"]].copy()
    fig_scatter = px.scatter(
        scatter,
        x="monthly_usage_count",
        y="monthly_equivalent_cost",
        color="review_priority",
        hover_name="user_id",
        title="Subscription cost vs. usage",
        labels={"monthly_usage_count": "Monthly uses", "monthly_equivalent_cost": "Monthly equivalent cost ($)"},
    )
    fig_scatter.update_layout(template="plotly_white")
    st.plotly_chart(fig_scatter, use_container_width=True)

with right_col:
    cycle_spend = (
        filtered.groupby("billing_cycle", as_index=False)["monthly_equivalent_cost"]
        .sum()
        .sort_values("monthly_equivalent_cost", ascending=False)
    )
    fig_cycle = px.pie(
        cycle_spend,
        names="billing_cycle",
        values="monthly_equivalent_cost",
        title="Spend by billing cycle",
        hole=0.45,
    )
    fig_cycle.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_cycle, use_container_width=True)

st.markdown("---")

review_table = (
    filtered["review_priority"].notna()
)

st.subheader("Priority review candidates")
review_candidates_df = filtered[
    [
        "user_id",
        "subscription_name",
        "category",
        "monthly_equivalent_cost",
        "monthly_usage_count",
        "review_priority",
        "potential_savings",
    ]
].sort_values(["review_priority", "potential_savings"], ascending=[False, False])

st.dataframe(review_candidates_df.head(25), use_container_width=True)

st.subheader("Budget pressure overview")
budget_pressure_table = user_budget_pressure.sort_values("budget_gap", ascending=False).head(20)
st.dataframe(
    budget_pressure_table[["user_id", "monthly_budget", "total_spend", "budget_gap"]].rename(
        columns={
            "monthly_budget": "Monthly budget",
            "total_spend": "Current spend",
            "budget_gap": "Budget gap",
        }
    ),
    use_container_width=True,
)

with st.expander("Business insights"):
    st.markdown(
        f"- Total monitored spending is ${filtered['monthly_equivalent_cost'].sum():,.2f} across {filtered.shape[0]} subscriptions.\n"
        f"- Average monthly equivalent cost is ${filtered['monthly_equivalent_cost'].mean():,.2f}.\n"
        f"- {low_usage_count} subscriptions are running with 2 or fewer uses per month, making them good review candidates.\n"
        f"- {budget_overrun_users} users are currently above their monthly budget.\n"
        f"- {review_candidates} subscriptions are flagged as high-priority review items."
    )
