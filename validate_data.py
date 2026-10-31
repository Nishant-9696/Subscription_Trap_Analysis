import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "subscriptions_raw.csv"
CLEAN_PATH = ROOT / "subscriptions_clean.csv"


with RAW_PATH.open("r", newline="", encoding="utf-8") as f:
    raw_rows = list(csv.DictReader(f))
with CLEAN_PATH.open("r", newline="", encoding="utf-8") as f:
    clean_rows = list(csv.DictReader(f))

raw_count = len(raw_rows)
clean_count = len(clean_rows)
missing_values = 0
invalid_rows = 0
duplicate_keys = []
seen = set()
for row in raw_rows:
    key = (row.get("user_id", ""), row.get("subscription_id", ""), row.get("subscription_name", ""), row.get("renewal_date", ""))
    if key in seen:
        duplicate_keys.append(key)
    seen.add(key)
    if any(str(v).strip() == "" for v in row.values()):
        missing_values += 1
    try:
        float(row.get("monthly_cost", "0"))
    except ValueError:
        invalid_rows += 1

invalid_status = sum(1 for row in raw_rows if str(row.get("subscription_status", "")).strip().lower() not in {"active", "paused", "trial", "cancelled"})
invalid_billing = sum(1 for row in raw_rows if str(row.get("billing_cycle", "")).strip().lower() not in {"monthly", "quarterly", "annual"})

# Check cleaned data quality.
clean_missing = sum(1 for row in clean_rows if any(str(v).strip() == "" for v in row.values()))
clean_invalid_costs = sum(1 for row in clean_rows if float(row.get("monthly_equivalent_cost", 0)) < 0)

print("Subscription data validation summary")
print("- Raw rows:", raw_count)
print("- Clean rows:", clean_count)
print("- Duplicate raw rows removed:", len(duplicate_keys))
print("- Raw rows with blank fields:", missing_values)
print("- Raw rows with invalid cost value:", invalid_rows)
print("- Raw rows with unrecognized status:", invalid_status)
print("- Raw rows with unrecognized billing cycle:", invalid_billing)
print("- Clean rows with blank fields:", clean_missing)
print("- Clean rows with negative equivalent cost:", clean_invalid_costs)
print("- Dataset validation status:", "PASS" if clean_count > 0 and clean_missing == 0 and clean_invalid_costs == 0 else "CHECK")
