import csv
import random
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parent
RAW_CSV = ROOT / "subscriptions_raw.csv"
CLEAN_CSV = ROOT / "subscriptions_clean.csv"
WORKBOOK = ROOT / "Subscription_Trap_Analysis.xlsx"

CATEGORIES = [
    "Entertainment",
    "Music",
    "Education",
    "Fitness",
    "Productivity",
    "Cloud Storage",
    "Gaming",
]

SUBSCRIPTIONS_BY_CATEGORY = {
    "Entertainment": ["Netflix", "Hulu", "Disney+", "Prime Video", "Crunchyroll", "Max"],
    "Music": ["Spotify", "Apple Music", "YouTube Music", "Tidal", "Amazon Music"],
    "Education": ["Coursera", "Udemy", "LinkedIn Learning", "Skillshare", "EdX"],
    "Fitness": ["Peloton", "Strava Summit", "Planet Fitness", "ClassPass", "Nike Training Club"],
    "Productivity": ["Notion", "Dropbox", "Adobe Creative Cloud", "Slack", "Canva Pro"],
    "Cloud Storage": ["Google One", "iCloud+", "Dropbox Plus", "Microsoft OneDrive", "pCloud"],
    "Gaming": ["Xbox Game Pass", "PlayStation Plus", "Nintendo Switch Online", "EA Play", "Steam Deck Cloud"],
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Apple Pay", "Bank Transfer"]
STATUSES = ["active", "paused", "trial", "cancelled"]
BILLING_CYCLES = ["monthly", "quarterly", "annual"]


rng = random.Random(42)


def random_date(start_year: int, end_year: int) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def normalize_status(value: str) -> str:
    if not value:
        return "active"
    value = value.strip().lower()
    if value in {"active", "current", "enabled"}:
        return "active"
    if value in {"paused", "suspended"}:
        return "paused"
    if value in {"trial", "free trial"}:
        return "trial"
    if value in {"cancelled", "canceled", "inactive"}:
        return "cancelled"
    return "active"


def normalize_cycle(value: str) -> str:
    if not value:
        return "monthly"
    v = value.strip().lower()
    aliases = {
        "monthly": "monthly",
        "month": "monthly",
        "monthlyly": "monthly",
        "quarterly": "quarterly",
        "quarter": "quarterly",
        "annual": "annual",
        "yearly": "annual",
        "year": "annual",
    }
    return aliases.get(v, "monthly")


def compute_monthly_equiv(cost: float, cycle: str) -> float:
    if cycle == "quarterly":
        return round(cost / 3, 2)
    if cycle == "annual":
        return round(cost / 12, 2)
    return round(cost, 2)


# Raw data generation

def generate_user_budget() -> float:
    return round(rng.uniform(30, 180), 2)


def build_subscription_row(user_id: str, user_budget: float, sub_index: int):
    category = rng.choices(
        CATEGORIES,
        weights=[24, 18, 16, 15, 17, 12, 10],
        k=1,
    )[0]
    service = rng.choice(SUBSCRIPTIONS_BY_CATEGORY[category])
    base_cost = {
        "Entertainment": rng.uniform(8, 24),
        "Music": rng.uniform(5, 19),
        "Education": rng.uniform(12, 45),
        "Fitness": rng.uniform(18, 78),
        "Productivity": rng.uniform(7, 28),
        "Cloud Storage": rng.uniform(4, 32),
        "Gaming": rng.uniform(9, 30),
    }[category]

    cycle = rng.choices(BILLING_CYCLES, weights=[65, 20, 15], k=1)[0]
    status = rng.choices(STATUSES, weights=[75, 9, 6, 10], k=1)[0]
    monthly_usage = max(0, int(rng.gauss(10, 8)))
    if rng.random() < 0.12:
        monthly_usage = int(rng.uniform(0, 2))
    if rng.random() < 0.05:
        status = "cancelled"

    start_date = random_date(2022, 2025)
    if cycle == "monthly":
        renewal_date = start_date + timedelta(days=30)
    elif cycle == "quarterly":
        renewal_date = start_date + timedelta(days=90)
    else:
        renewal_date = start_date + timedelta(days=365)

    row = {
        "user_id": user_id,
        "subscription_id": f"SUB{1000 + sub_index:06d}",
        "subscription_name": service,
        "category": category,
        "monthly_cost": round(base_cost, 2),
        "billing_cycle": cycle,
        "start_date": start_date.isoformat(),
        "renewal_date": renewal_date.isoformat(),
        "monthly_usage_count": monthly_usage,
        "subscription_status": status,
        "monthly_budget": round(user_budget, 2),
        "payment_method": rng.choice(PAYMENT_METHODS),
    }
    return row


def create_raw_dataset():
    records = []
    for user_num in range(1, 201):
        user_id = f"U{user_num:03d}"
        budget = generate_user_budget()
        for i in range(1, 6):
            row = build_subscription_row(user_id, budget, (user_num - 1) * 5 + i)
            records.append(row)

    # Inject realistic data-quality issues for the raw dataset.
    # Duplicates
    for idx in range(15):
        records.append(records[idx].copy())

    # Missing and invalid values.
    for idx in [20, 63, 100, 120, 155, 190, 232, 280, 330, 355, 400, 440, 460, 500, 630, 700, 780, 860, 930, 970]:
        if idx < len(records):
            records[idx]["subscription_name"] = ""
            records[idx]["payment_method"] = ""
            records[idx]["monthly_usage_count"] = ""

    for idx in [50, 180, 310, 440, 680, 810, 990]:
        if idx < len(records):
            records[idx]["monthly_cost"] = "-5.00"
            records[idx]["billing_cycle"] = "yearly"
            records[idx]["subscription_status"] = "NOT_VALID"

    for idx in [90, 220, 360, 510, 760]:
        if idx < len(records):
            records[idx]["monthly_budget"] = ""
            records[idx]["renewal_date"] = "2025-99-99"

    # Force a few rows with low usage but high cost for anomaly analysis.
    for idx in [110, 420, 730, 820, 950]:
        if idx < len(records):
            records[idx]["monthly_usage_count"] = 0
            records[idx]["monthly_cost"] = round(records[idx]["monthly_cost"] * 1.7, 2)

    # Make some cancellation/paused rows inconsistent.
    for idx in [145, 370, 640, 920]:
        if idx < len(records):
            records[idx]["subscription_status"] = "Cancelled"

    return records


def clean_raw_dataset(raw_rows):
    cleaned = []
    seen = set()
    for row in raw_rows:
        user_id = str(row.get("user_id", "")).strip()
        subscription_id = str(row.get("subscription_id", "")).strip()
        if not user_id or not subscription_id:
            continue

        signature = (user_id, subscription_id, str(row.get("subscription_name", "")).strip(), str(row.get("renewal_date", "")).strip())
        if signature in seen:
            continue
        seen.add(signature)

        # Standardize field values.
        cleaned_row = {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "subscription_name": str(row.get("subscription_name", "")).strip() or "Unspecified Service",
            "category": str(row.get("category", "")).strip() or "Other",
            "monthly_cost": row.get("monthly_cost", "0"),
            "billing_cycle": normalize_cycle(str(row.get("billing_cycle", "monthly"))),
            "start_date": str(row.get("start_date", "")).strip() or "2024-01-01",
            "renewal_date": str(row.get("renewal_date", "")).strip() or "2025-01-01",
            "monthly_usage_count": row.get("monthly_usage_count", "0"),
            "subscription_status": normalize_status(str(row.get("subscription_status", "active"))),
            "monthly_budget": row.get("monthly_budget", "0"),
            "payment_method": str(row.get("payment_method", "Credit Card")).strip() or "Credit Card",
        }

        # Fix invalid dates and costs.
        try:
            datetime.strptime(cleaned_row["start_date"], "%Y-%m-%d")
        except ValueError:
            cleaned_row["start_date"] = "2024-01-01"

        try:
            datetime.strptime(cleaned_row["renewal_date"], "%Y-%m-%d")
        except ValueError:
            cleaned_row["renewal_date"] = "2025-01-01"

        try:
            monthly_cost = float(cleaned_row["monthly_cost"])
            if monthly_cost < 0:
                monthly_cost = abs(monthly_cost)
        except (TypeError, ValueError):
            monthly_cost = 0.0
        cleaned_row["monthly_cost"] = round(monthly_cost, 2)

        try:
            usage = int(float(cleaned_row["monthly_usage_count"]))
            if usage < 0:
                usage = abs(usage)
        except (TypeError, ValueError):
            usage = 0
        cleaned_row["monthly_usage_count"] = usage

        try:
            budget = float(cleaned_row["monthly_budget"])
            if budget <= 0:
                budget = 60.0
        except (TypeError, ValueError):
            budget = 60.0
        cleaned_row["monthly_budget"] = round(budget, 2)

        cleaned_row["monthly_equivalent_cost"] = compute_monthly_equiv(cleaned_row["monthly_cost"], cleaned_row["billing_cycle"])
        cleaned_row["budget_contribution_pct"] = round((cleaned_row["monthly_equivalent_cost"] / cleaned_row["monthly_budget"]) * 100, 2) if cleaned_row["monthly_budget"] else 0
        cleaned_row["review_priority"] = "Low Priority"
        if cleaned_row["monthly_equivalent_cost"] >= 32 and cleaned_row["monthly_usage_count"] <= 2:
            cleaned_row["review_priority"] = "High Priority"
        elif cleaned_row["monthly_equivalent_cost"] >= 20 and cleaned_row["monthly_usage_count"] <= 5:
            cleaned_row["review_priority"] = "Medium Priority"
        cleaned_row["potential_savings"] = round(cleaned_row["monthly_equivalent_cost"] * 0.6, 2) if cleaned_row["review_priority"] != "Low Priority" else round(cleaned_row["monthly_equivalent_cost"] * 0.25, 2)

        cleaned.append(cleaned_row)

    return cleaned


def write_csv(rows, filepath):
    fieldnames = [
        "user_id",
        "subscription_id",
        "subscription_name",
        "category",
        "monthly_cost",
        "billing_cycle",
        "start_date",
        "renewal_date",
        "monthly_usage_count",
        "subscription_status",
        "monthly_budget",
        "payment_method",
    ]
    extra_fields = ["monthly_equivalent_cost", "budget_contribution_pct", "review_priority", "potential_savings"]
    all_fields = fieldnames + extra_fields

    with filepath.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in all_fields})


def write_business_insights(clean_rows):
    from collections import defaultdict

    total_monthly_spend = round(sum(float(r.get("monthly_equivalent_cost", 0)) for r in clean_rows), 2)
    avg_cost = round(total_monthly_spend / len(clean_rows), 2) if clean_rows else 0
    low_usage_active = sum(1 for r in clean_rows if int(r.get("monthly_usage_count", 0)) <= 2 and r.get("subscription_status") == "active")
    high_priority = sum(1 for r in clean_rows if r.get("review_priority") == "High Priority")

    category_spend = defaultdict(float)
    for r in clean_rows:
        category_spend[r.get("category", "Other")] += float(r.get("monthly_equivalent_cost", 0))
    sorted_categories = sorted(category_spend.items(), key=lambda x: x[1], reverse=True)

    user_spend = defaultdict(float)
    user_budget = {}
    for r in clean_rows:
        user_spend[r["user_id"]] += float(r.get("monthly_equivalent_cost", 0))
        user_budget[r["user_id"]] = float(r.get("monthly_budget", 0))
    over_budget_users = sum(1 for uid, spend in user_spend.items() if spend > user_budget.get(uid, 0))
    top_review = sorted(clean_rows, key=lambda r: float(r.get("potential_savings", 0)), reverse=True)[:5]

    lines = [
        "# Subscription Trap Analysis: Business Insights",
        "",
        "This analysis uses synthetic data only for demonstration. The dataset contains 1,000 cleaned subscription records across 200 users and is intended to support a practical review of recurring subscription spend.",
        "",
        "## Executive Summary",
        "",
        "- Total monthly-equivalent subscription spend: $%.2f" % total_monthly_spend,
        "- Average monthly cost per active subscription: $%.2f" % avg_cost,
        "- Active subscriptions with low reported usage (<=2 uses/month): %d" % low_usage_active,
        "- Users exceeding their monthly budget: %d" % over_budget_users,
        "- High-priority subscription reviews flagged: %d" % high_priority,
        "",
        "## Key Findings",
        "",
        "1. Category spend is concentrated in fitness and education. The top category is %s with $%.2f in monthly-equivalent spending, followed by %s with $%.2f." % (sorted_categories[0][0], sorted_categories[0][1], sorted_categories[1][0], sorted_categories[1][1]),
        "2. %d active subscriptions have low reported usage, which indicates a review opportunity but not automatic waste. The trigger is based on both low usage and the subscription's cost profile." % low_usage_active,
        "3. %d users exceed their budget, which suggests that the budget control signal is useful when evaluating account-level subscription pressure." % over_budget_users,
        "4. The highest-priority subscriptions are those with a combination of high monthly-equivalent cost and low usage. This review-first list is captured in the workbook's review logic and in the SQL analysis queries." ,
        "",
        "## Top review candidates",
        "",
    ]
    for item in top_review:
        lines.append(f"- {item.get('subscription_name', 'Unknown service')} ({item.get('category', 'Unknown category')}) for user {item.get('user_id', 'Unknown')} — monthly equivalent: ${float(item.get('monthly_equivalent_cost', 0)):.2f}, potential savings scenario: ${float(item.get('potential_savings', 0)):.2f}.")
    lines.extend([
        "",
        "## Supporting project assets",
        "",
        "- Raw data file: subscriptions_raw.csv",
        "- Cleaned data file: subscriptions_clean.csv",
        "- Excel workbook: Subscription_Trap_Analysis.xlsx",
        "- SQL scripts: 01_create_database.sql to 06_advanced_analysis.sql",
        "",
        "The analysis is intentionally based on synthetic, non-personal data and all savings estimates are scenario-based cancellation values rather than guaranteed savings.",
        "",
    ])
    (ROOT / "business_insights.md").write_text("\n".join(lines), encoding="utf-8")


def write_xlsx(raw_rows, clean_rows):
    wb = Workbook()
    ws_raw = wb.active
    ws_raw.title = "Raw_Data"

    raw_fields = list(raw_rows[0].keys()) if raw_rows else [
        "user_id",
        "subscription_id",
        "subscription_name",
        "category",
        "monthly_cost",
        "billing_cycle",
        "start_date",
        "renewal_date",
        "monthly_usage_count",
        "subscription_status",
        "monthly_budget",
        "payment_method",
    ]
    ws_raw.append(raw_fields)
    for row in raw_rows:
        ws_raw.append([row.get(field, "") for field in raw_fields])
    ws_raw.freeze_panes = "A2"
    ws_raw.auto_filter.ref = f"A1:{ws_raw.cell(row=1, column=len(raw_fields)).coordinate}"

    ws_clean = wb.create_sheet("Cleaned_Data")
    clean_fields = list(clean_rows[0].keys()) if clean_rows else [
        "user_id",
        "subscription_id",
        "subscription_name",
        "category",
        "monthly_cost",
        "billing_cycle",
        "start_date",
        "renewal_date",
        "monthly_usage_count",
        "subscription_status",
        "monthly_budget",
        "payment_method",
        "monthly_equivalent_cost",
        "budget_contribution_pct",
        "review_priority",
        "potential_savings",
    ]
    ws_clean.append(clean_fields)
    for row in clean_rows:
        ws_clean.append([row.get(field, "") for field in clean_fields])
    ws_clean.freeze_panes = "A2"
    ws_clean.auto_filter.ref = f"A1:{ws_clean.cell(row=1, column=len(clean_fields)).coordinate}"

    # Data quality report
    ws_quality = wb.create_sheet("Data_Quality_Report")
    ws_quality.append(["Metric", "Value"])
    total_raw = len(raw_rows)
    total_clean = len(clean_rows)
    missing_values = 0
    duplicate_rows = 0
    invalid_rows = 0
    for row in raw_rows:
        if any(str(v).strip() == "" for v in row.values()):
            missing_values += 1
        if row.get("billing_cycle") in {"yearly", "NOT_VALID"}:
            invalid_rows += 1
        if row.get("monthly_usage_count") in {"", "-5", "-30", "N/A"}:
            invalid_rows += 1
    seen = set()
    for row in raw_rows:
        key = (row.get("user_id"), row.get("subscription_id"), row.get("subscription_name"), row.get("renewal_date"))
        if key in seen:
            duplicate_rows += 1
        seen.add(key)

    ws_quality.append(["Raw rows", total_raw])
    ws_quality.append(["Clean rows", total_clean])
    ws_quality.append(["Duplicates removed", duplicate_rows])
    ws_quality.append(["Missing/blank values", missing_values])
    ws_quality.append(["Invalid records corrected", invalid_rows])
    ws_quality.append(["Rows retained after cleaning", total_clean])
    ws_quality.append(["Did not pass validation", max(total_raw - total_clean, 0)])
    ws_quality.append([])
    ws_quality.append(["Correction Notes", "Duplicate rows removed; blank names and payment methods set to defaults; invalid dates normalized; negative costs converted to absolute values; invalid monthly usage set to 0."])

    # Spending analysis by category
    ws_spend = wb.create_sheet("Spending_Analysis")
    ws_spend.append(["Category", "Total Monthly-Equivalent Spend", "Avg Monthly Cost", "Active Subscriptions", "Low-Usage Count"])
    for category in CATEGORIES:
        ws_spend.append([
            category,
            f"=SUMIFS(Cleaned_Data!$M$2:$M$1048576,Cleaned_Data!$D$2:$D$1048576,A{ws_spend.max_row})",
            f"=IFERROR(AVERAGEIF(Cleaned_Data!$D$2:$D$1048576,A{ws_spend.max_row},Cleaned_Data!$M$2:$M$1048576),0)",
            f"=COUNTIFS(Cleaned_Data!$D$2:$D$1048576,A{ws_spend.max_row},Cleaned_Data!$J$2:$J$1048576,\"active\")",
            f"=COUNTIFS(Cleaned_Data!$D$2:$D$1048576,A{ws_spend.max_row},Cleaned_Data!$I$2:$I$1048576,\"<=2\")",
        ])

    # Underused subscriptions summary
    ws_underused = wb.create_sheet("Underused_Subscriptions")
    ws_underused.append(["User ID", "Subscription", "Category", "Monthly Equivalent Cost", "Monthly Usage", "Review Priority", "Potential Saving"])
    underused_rows = [
        row for row in clean_rows if row.get("monthly_usage_count", 0) <= 2 and row.get("monthly_equivalent_cost", 0) >= 10
    ]
    for row in underused_rows[:100]:
        ws_underused.append([
            row.get("user_id", ""),
            row.get("subscription_name", ""),
            row.get("category", ""),
            row.get("monthly_equivalent_cost", ""),
            row.get("monthly_usage_count", ""),
            row.get("review_priority", ""),
            row.get("potential_savings", ""),
        ])

    # Renewal analysis
    ws_renewal = wb.create_sheet("Renewal_Analysis")
    ws_renewal.append(["Subscription", "User ID", "Renewal Date", "Monthly Equivalent Cost", "Status", "Days Until Renewal"])
    for row in sorted(clean_rows, key=lambda x: x.get("renewal_date", "2025-01-01"))[:150]:
        try:
            renewal_date = datetime.strptime(row.get("renewal_date", "2025-01-01"), "%Y-%m-%d").date()
            days = (renewal_date - date.today()).days
        except ValueError:
            days = 0
        ws_renewal.append([
            row.get("subscription_name", ""),
            row.get("user_id", ""),
            row.get("renewal_date", ""),
            row.get("monthly_equivalent_cost", ""),
            row.get("subscription_status", ""),
            days,
        ])

    # Budget analysis
    ws_budget = wb.create_sheet("Budget_Analysis")
    ws_budget.append(["User ID", "Monthly Budget", "Actual Monthly Spend", "Budget Difference", "Status"])
    user_rows = {}
    for row in clean_rows:
        user_rows.setdefault(row["user_id"], 0)
        user_rows[row["user_id"]] += float(row.get("monthly_equivalent_cost", 0))
    unique_users = sorted(user_rows)
    for idx, user_id in enumerate(unique_users, start=2):
        budget_formula = f"=XLOOKUP(A{idx},Cleaned_Data!$A$2:$A$1001,Cleaned_Data!$K$2:$K$1001,0)"
        spend_formula = f"=SUMIF(Cleaned_Data!$A$2:$A$1001,A{idx},Cleaned_Data!$M$2:$M$1001)"
        diff_formula = f"=C{idx}-B{idx}"
        status_formula = f"=IF(C{idx}>B{idx},\"Over Budget\",\"Within Budget\")"
        ws_budget.append([user_id, budget_formula, spend_formula, diff_formula, status_formula])

    # Executive Summary
    ws_summary = wb.create_sheet("Executive_Summary")
    ws_summary.append(["Metric", "Value"])
    total_monthly_spend = round(sum(float(r.get("monthly_equivalent_cost", 0)) for r in clean_rows), 2)
    avg_monthly_cost = round(total_monthly_spend / len(clean_rows), 2) if clean_rows else 0
    underused = sum(1 for r in clean_rows if r.get("monthly_usage_count", 0) <= 2 and r.get("subscription_status") == "active")
    over_budget_users = sum(1 for row in ws_budget.iter_rows(min_row=2, values_only=True) if row[2] > row[1])
    high_priority = sum(1 for r in clean_rows if r.get("review_priority") == "High Priority")

    ws_summary.append(["Total monthly-equivalent spend", total_monthly_spend])
    ws_summary.append(["Average monthly cost per active subscription", avg_monthly_cost])
    ws_summary.append(["Active subscriptions with low usage", underused])
    ws_summary.append(["Users over budget", over_budget_users])
    ws_summary.append(["High-priority review subscriptions", high_priority])
    ws_summary.append(["Dummy note", "Potential monthly savings are scenario-based and not guaranteed."])
    ws_summary["A1"].font = Font(bold=True)
    ws_summary["A1"].fill = PatternFill("solid", fgColor="D9EAF7")

    # Add charts on summary sheets
    spend_chart = BarChart()
    spend_chart.type = "bar"
    spend_chart.style = 10
    spend_chart.title = "Category Spending"
    spend_chart.y_axis.title = "Monthly Equivalent Cost"
    spend_chart.x_axis.title = "Category"
    chart_data = Reference(ws_spend, min_col=2, min_row=1, max_row=8, max_col=2)
    chart_cats = Reference(ws_spend, min_col=1, min_row=2, max_row=8)
    spend_chart.add_data(chart_data, titles_from_data=True)
    spend_chart.set_categories(chart_cats)
    ws_spend.add_chart(spend_chart, "E3")

    budget_chart = LineChart()
    budget_chart.title = "Budget vs Actual Spend"
    budget_chart.y_axis.title = "USD"
    budget_chart.x_axis.title = "User"
    budget_values = Reference(ws_budget, min_col=3, min_row=1, max_row=ws_budget.max_row)
    budget_budgets = Reference(ws_budget, min_col=2, min_row=1, max_row=ws_budget.max_row)
    budget_chart.add_data(budget_values, titles_from_data=True)
    budget_chart.add_data(budget_budgets, titles_from_data=True)
    ws_budget.add_chart(budget_chart, "F3")

    pie = PieChart()
    pie.title = "Priority Distribution"
    priority_counts = Counter(r.get("review_priority", "Low Priority") for r in clean_rows)
    pk = list(priority_counts.keys())
    pv = list(priority_counts.values())
    ws_priority = wb.create_sheet("Priority_Overview")
    ws_priority.append(["Review Priority", "Count"])
    for key in ["High Priority", "Medium Priority", "Low Priority"]:
        ws_priority.append([key, priority_counts.get(key, 0)])
    pie_data = Reference(ws_priority, min_col=2, min_row=1, max_row=4)
    pie_cats = Reference(ws_priority, min_col=1, min_row=2, max_row=4)
    pie.add_data(pie_data, titles_from_data=True)
    pie.set_categories(pie_cats)
    ws_priority.add_chart(pie, "E3")

    # Set a few formatting improvements.
    for sheet in [ws_raw, ws_clean, ws_quality, ws_spend, ws_underused, ws_renewal, ws_budget, ws_summary, ws_priority]:
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="center")

    ws_spend["A1"].font = Font(bold=True)
    ws_underused["A1"].font = Font(bold=True)
    ws_renewal["A1"].font = Font(bold=True)
    ws_budget["A1"].font = Font(bold=True)
    ws_summary["A1"].font = Font(bold=True)

    wb.save(WORKBOOK)
    write_business_insights(clean_rows)


# Main generation flow.
raw_rows = create_raw_dataset()
clean_rows = clean_raw_dataset(raw_rows)
write_csv(raw_rows, RAW_CSV)
write_csv(clean_rows, CLEAN_CSV)
write_xlsx(raw_rows, clean_rows)

# Print a short summary for the user.
print(f"Generated {len(raw_rows)} raw records and {len(clean_rows)} cleaned rows.")
print(f"Workbook saved to: {WORKBOOK}")
print(f"Raw CSV saved to: {RAW_CSV}")
print(f"Clean CSV saved to: {CLEAN_CSV}")
print(f"Estimated total monthly spend: ${sum(float(r.get('monthly_equivalent_cost', 0)) for r in clean_rows):,.2f}")
