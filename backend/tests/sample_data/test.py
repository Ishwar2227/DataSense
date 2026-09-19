import pandas as pd
import os

from app.cleaning.category_matcher import normalize_category_column
from app.cleaning.currency_normalizer import normalize_currency_column
from app.cleaning.pipeline import clean_dataframe
from app.analysis.trends import compute_monthly_trend
from app.analysis.change_detection import find_top_contributors
from app.analysis.anomaly_detection import detect_outliers

from app.analysis.insights_builder import build_insights
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "..", "..", "..", "sample_db", "Superstore.csv")

# df = pd.read_csv(csv_path, encoding="cp1252")
df = pd.read_csv(csv_path, encoding="cp1252")
df = df.sample(n=min(20_000, len(df)), random_state=42)
# --- Test 1: Category cleaning ---
print("=" * 40)
print("TEST 1: Category normalization")
print("=" * 40)
for col in ["Category", "Sub-Category", "Customer Name"]:
    cleaned, log = normalize_category_column(df[col])
    print(f"--- {col} ---")
    print("Unique values after cleaning:", cleaned.nunique())
    print("Merge log:", log)
    print()

# --- Test 2: Currency cleaning ---
print("=" * 40)
print("TEST 2: Currency normalization")
print("=" * 40)
cleaned_sales, failed = normalize_currency_column(df["Sales"])
print("Sample cleaned values:")
print(cleaned_sales.head())
print("Failed conversions:", failed)
print()

# --- Test 3: Monthly trend (runs the FULL cleaning pipeline once) ---
print("=" * 40)
print("TEST 3: Monthly sales trend")
print("=" * 40)
cleaned_df, report = clean_dataframe(df)
trend = compute_monthly_trend(cleaned_df, "Order Date", "Sales")
print(trend.to_string())


print("=" * 40)
print("TEST 4: Top contributors to change (Region)")
print("=" * 40)
contributors = find_top_contributors(cleaned_df, "Order Date", "Sales", "Region", "2017-03", "2017-02")
for row in contributors:
    print(row)



print("=" * 40)
print("TEST 5: Outlier detection (Sales)")
print("=" * 40)
outliers = detect_outliers(cleaned_df, "Sales", threshold=3.0)
print(f"Found {len(outliers)} outlier rows")
for row in outliers[:5]:  # just print first 5 to keep it readable
    print(f"Order ID: {row['Order ID']}, Sales: {row['Sales']}, Z-score: {row['z_score']:.2f}")



print("=" * 40)
print("TEST 6: Full insights object (auto column selection)")
print("=" * 40)
insights = build_insights(cleaned_df, report["column_types"])
print(f"Selected columns: {insights.get('selected_columns')}")
print(f"Latest month: {insights.get('latest_month')}, Previous: {insights.get('previous_month')}")
print(f"Outlier count: {insights.get('outlier_count')}")
print("Top contributors:")
for row in insights.get("top_contributors", []):
    print(row)


from app.analysis.column_selector import select_analysis_columns
from app.cleaning.pipeline import clean_dataframe

print("=" * 40)
print("TEST 7: Auto column selection")
print("=" * 40)
cleaned_df, report = clean_dataframe(df)
selected = select_analysis_columns(cleaned_df, report["column_types"])
print(selected)