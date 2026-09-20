# DataSense — Analysis Rules

## 1. Purpose

Define how DataSense automatically selects analysis columns
and generates business insights from cleaned data.

## 2. Automatic Column Selection

DataSense dynamically selects:

- Date column → used for time-based analysis
- Value column → numeric/currency measure used for analysis
- Group column → categorical dimension used for comparisons

Column selection is heuristic and does not assume a fixed dataset schema.

## 3. Date Column Selection

DataSense first considers columns inferred as `date`.

If multiple date columns exist:

- Prefer a valid date column.
- Prefer the date column with fewer missing values in the representative sample.

A date column is not required for every analysis. Datasets without a usable date column can still receive value-based and anomaly analysis.

## 4. Value Column Selection

DataSense considers columns inferred as:

- `currency`
- `decimal`
- `quantity`

Obvious identifiers, geographic codes, coordinates, and similar fields are excluded.

Candidate value columns are scored using several signals:

### Strong semantic signals

Names containing terms such as:

- sales
- revenue
- amount
- total
- value
- profit
- income
- price
- cost
- spend
- rating
- score
- duration

receive a positive preference.

### Weak metric signals

Names containing terms such as:

- id
- code
- number
- row
- index
- season
- episode
- rank
- year
- month
- day
- quantity
- votes

are penalized because they are often identifiers, dimensions, or supporting measurements rather than the primary business metric.

### Data quality signals

The selector also considers:

- number of unique values
- numeric coverage
- variation in the sampled values
- inferred type

Currency columns receive an additional preference when otherwise suitable.

The highest-scoring suitable candidate is selected.

## 5. Group Column Selection

Group columns must primarily be inferred as:

- `category`
- `text`

The selector rejects obvious identifier/free-text columns such as:

- ID
- code
- number
- name
- address
- phone
- email
- description
- invoice
- stock
- SKU

Group cardinality is also considered.

### Preferred groups

DataSense gives additional preference to meaningful business dimensions such as:

- Region
- Segment
- Category
- Department
- Type
- Class
- Country
- State
- City
- Group
- Property
- Status
- Gender
- Customer Type

Preferred groups can contain up to approximately 100 unique values.

Other categorical/text groups are limited to approximately 20 unique values.

Smaller chart-friendly group counts receive a slight preference.

## 6. Monthly Trend Analysis

When both a date column and value column are available:

1. Convert dates to monthly periods.
2. Group records by month.
3. Sum the selected value.
4. Sort chronologically.
5. Calculate month-over-month percentage change.

Formula:

```text
change_pct = ((current_month - previous_month)
              / previous_month) × 100
```

## 7. Latest and Previous Month
### DataSense identifies:
- latest available month
- previous available month
These values are used for comparison-based insights.
If there are not at least two usable periods, change analysis is unavailable.
## 8. Top Contributors
### When date, value, and group columns are available:
- Compare the selected value for the latest month against the previous month.
- Calculate absolute change.
- Calculate percentage change.
- Identify the group with the largest change.
The result is based on the available data and does not claim a causal explanation.
## 9. Outlier Detection
DataSense detects unusually large or small values using a Z-score based approach.
Current threshold:
```bash
|Z-score| >= 3.0
```
Outlier records are returned with their Z-score.
A statistical outlier is not automatically considered an error.

## 10. Insight Availability
Different datasets can support different analyses.
For example:
- Date + value → trend/change analysis
- Date + value + group → contributor analysis
- Value → anomaly analysis
- No usable value → value-based analysis unavailable
DataSense reports unavailable analyses instead of inventing results.


## 11. Question Statistics
For supported business questions, DataSense prepares structured statistics before generating a natural-language answer.
Current supported question intents include:
- Why did the value change?
- Which group changed the most?
- Are there any anomalies?
The question-answering layer receives these trusted statistics rather than performing unrestricted calculations over the raw dataset.

## 12. JSON Safety
Analysis results must be JSON serializable so they can be returned safely through the FastAPI API.
Invalid numeric values such as NaN or infinity are sanitized before API responses are returned.

## 13. Limitations
- Automatic column selection is heuristic.
- A dataset may contain multiple equally valid analysis measures.
- The selected measure may not always represent the business metric a human analyst would choose.
- Correlation does not imply causation.
- Statistical outliers are not necessarily errors.
- Business meaning depends on dataset context.
- Datasets without sufficient columns cannot support every analysis.
