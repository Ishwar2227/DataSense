# DataSense — Phase 5 Benchmark Results

## Overview

Phase 5 validates DataSense against a broader set of real-world e-commerce and retail CSV datasets rather than relying only on the original development datasets.

The benchmark evaluates:

- Column type inference accuracy
- Whether datasets can produce usable DataSense insights
- Pipeline failures
- Cleaning changes logged by the pipeline
- Average processing runtime

## Final Benchmark

| Metric | Result |
|---|---:|
| Datasets evaluated | **15** |
| Valid insights | **14 / 15** |
| Insufficient data | **1 / 15** |
| Pipeline errors | **0** |
| Column typing accuracy | **140 / 158 (88.61%)** |
| Datasets with cleaning changes logged | **4 / 15** |
| Total cleaning changes logged | **14** |
| Average runtime | **8.527 seconds** |

## Dataset Coverage

The benchmark used 15 e-commerce/retail datasets covering different schemas, sizes, column naming conventions, and data characteristics.

| Dataset | Result |
|---|---|
| BigMart.csv | Valid |
| data.csv | Valid |
| DataCoSupplyChainDataset.csv | Valid |
| DMart_sample_data.csv | Valid |
| E-Commerce DataSet.csv | Valid |
| events.csv | Insufficient data |
| olist_order_items_dataset.csv | Valid |
| online_shoppers_purchasing_intention.csv | Valid |
| orders.csv | Valid |
| Shop Direct Sale Data For Research.csv | Valid |
| Stores.csv | Valid |
| supermarket_sales - Sheet1.csv | Valid |
| Superstore.csv | Valid |
| train.csv | Valid |
| transaction_data.csv | Valid |

## Selected Analysis Columns

The benchmark confirmed that DataSense can dynamically select analysis columns across substantially different schemas.

Examples include:

- `data.csv` → `InvoiceDate`, `AnalysisValue`, `Country`
- `DMart_sample_data.csv` → `Date`, `Total`, `ProductCategory`
- `Superstore.csv` → `Order Date`, `Sales`, `Region`
- `supermarket_sales - Sheet1.csv` → `Date`, `Total`, `City`
- `Stores.csv` → no date column, `Revenue`, `Property`
- `transaction_data.csv` → no date column, `SALES_VALUE`, no group

Some datasets legitimately do not contain the fields required for every analysis. DataSense therefore marks those analyses as unavailable instead of inventing results.

## Insufficient Dataset

`events.csv` was classified as insufficient because the available schema did not provide a usable business value metric for the current DataSense analysis.

This is treated as an expected limitation rather than a pipeline failure.

The benchmark therefore records:

- `insufficient_data`: 1
- `pipeline_errors`: 0

## Column Typing

Final typing accuracy:

**140 / 158 columns = 88.61%**

The benchmark exposed several difficult real-world semantic cases, including:

- Numeric categorical fields
- Numeric identifiers
- Duration metrics
- Retail discount fields
- Encoded categorical fields
- Concatenated identifier names
- Columns whose meaning cannot be determined perfectly from values alone

The inference logic was improved during benchmarking and then intentionally stabilized rather than adding dataset-specific rules to force a perfect benchmark score.

The remaining mismatches are documented in:

`benchmarks/typing_mismatches.csv`

## Cleaning Results

The benchmark recorded cleaning changes made by the pipeline:

- **4 of 15 datasets** had cleaning changes logged.
- **14 total cleaning changes** were logged.

These numbers describe changes observed by the pipeline. They should **not** be interpreted as a percentage of all possible data-quality issues that DataSense successfully fixed.

A ground-truth catalogue of every possible cleaning issue was not part of this benchmark, so a true "percentage of cleaning issues automatically fixed" cannot be claimed from these tests.

## Performance

Average benchmark runtime:

**8.527 seconds per dataset**

The benchmark uses the full CSV files available in the benchmark collection and records runtime for each dataset.

Runtime naturally varies with dataset size and schema complexity.

## Benchmark Limitations

This benchmark is intended as an engineering validation set, not a statistically representative survey of all retail CSV files.

Important limitations:

1. The 15 datasets were selected as practical real-world test cases, not through a random sampling procedure.
2. Column typing is evaluated against the benchmark manifest's expected types.
3. Some columns are semantically ambiguous even for a human without additional metadata.
4. Cleaning accuracy cannot be expressed as a true percentage without independent ground truth for every cleaning issue.
5. "Valid insights" means the pipeline produced usable analysis structures; it does not mean every automatically selected metric or grouping dimension is guaranteed to be the ideal business interpretation.
6. The benchmark does not establish production-scale reliability for arbitrary future datasets.

## Phase 5 Exit Result

Phase 5 benchmarking is complete.

Final engineering result:

> **DataSense successfully processed 14 of 15 benchmark datasets with zero pipeline errors, achieved 88.61% column typing accuracy across 158 evaluated columns, logged 14 cleaning changes across 4 datasets, and averaged 8.527 seconds per dataset.**

The benchmark has now been documented with explicit limitations rather than presenting unsupported or inflated accuracy claims.
