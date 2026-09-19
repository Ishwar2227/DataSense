# DataSense — Analysis Rules

## 1. Purpose
Define how DataSense automatically selects analysis columns
and generates business insights from cleaned data.

## 2. Automatic Column Selection

DataSense selects:

- Date column → required for time-based analysis
- Value column → numeric/currency measure to analyze
- Group column → categorical column used to compare groups

## 3. Date Column Selection
If multiple date columns exist:
- Prefer a valid date column.
- Prefer the date column with fewer missing values.

## 4. Value Column Selection
If multiple numeric/currency columns exist:
- Select the most appropriate analysis measure.
- Current implementation prefers the currency column
  with the largest aggregate value.

## 5. Group Column Selection
Categorical columns are evaluated using cardinality.

Current rule:
- Prefer categorical columns with approximately 2–20 unique values.
- Prefer meaningful business grouping columns when possible.
- Use preferred keywords as a tie-breaker.

Examples:
- Region
- Country
- Category
- Segment

## 6. Monthly Trend Analysis
For the selected date and value columns:

1. Convert dates to monthly periods.
2. Group records by month.
3. Sum the selected value.
4. Sort chronologically.
5. Calculate month-over-month percentage change.

Formula:

change_pct = ((current_month - previous_month)
              / previous_month) × 100

## 7. Latest and Previous Month
DataSense identifies:
- latest available month
- previous available month

These values are used for comparison-based insights.

## 8. Top Contributors
When a group column exists:
- Compare the selected value for the latest month
  against the previous month.
- Calculate absolute change.
- Calculate percentage change.
- Rank groups by their contribution to change.

## 9. Outlier Detection
DataSense detects unusually large or small values
using a Z-score based approach.

Current threshold:

|Z-score| >= 3.0

Outlier records are returned with their Z-score.

## 10. Insight Output
The analysis result contains:

- selected columns
- monthly trend
- latest month
- previous month
- top contributors
- outlier count
- outlier records

## 11. JSON Safety
Analysis results must be JSON serializable so they can be
returned safely through the FastAPI API.

## 12. Limitations
- Automatic column selection is heuristic.
- A dataset may contain multiple equally valid analysis measures.
- Correlation does not imply causation.
- Statistical outliers are not necessarily errors.
- Business meaning depends on the dataset context.