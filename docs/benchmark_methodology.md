# DataSense — Benchmark Methodology

## 1. Purpose

This document describes how DataSense was benchmarked during Phase 5.

The purpose of the benchmark was to evaluate whether the general-purpose CSV analysis pipeline works across a diverse collection of retail and e-commerce datasets.

The benchmark was intended to measure:

- robustness across different schemas
- type-inference behavior
- cleaning behavior
- analysis availability
- pipeline reliability
- runtime

It was not intended to prove universal accuracy.

---

## 2. Benchmark Dataset Pool

The final benchmark pool contained **15 datasets**.

The datasets varied substantially in:

- row count
- column count
- naming conventions
- data types
- date availability
- business metrics
- identifier formats
- categorical fields
- dataset size

The final pool included datasets ranging from approximately one hundred rows to several million rows.

Examples included:

- retail transaction data
- online retail data
- supermarket sales
- e-commerce orders
- supply-chain data
- store-level revenue data
- customer purchasing data
- event data

This variety was important because DataSense is intended to operate on previously unseen CSV schemas.

---

## 3. Evaluation Philosophy

The benchmark followed a generalization-first approach.

The goal was not to create dataset-specific rules until every benchmark file produced a perfect result.

Instead, benchmark failures were examined for patterns that could justify **general improvements to the pipeline**.

A new rule was considered useful when it represented a broader data pattern rather than a one-off correction for a particular file.

---

## 4. What Was Evaluated

Each dataset passed through the normal DataSense pipeline.

The benchmark considered:

### 4.1 Type Inference

The inferred type of each relevant column was compared with the expected type used by the benchmark evaluation.

The tracked categories included types such as:

- text
- category
- date
- quantity
- decimal
- currency
- identifier

The final benchmark recorded:

```text
140 correct / 158 evaluated
```

which corresponds to:

```text
88.61% typing accuracy
```

---

### 4.2 Cleaning Behavior

The benchmark recorded cleaning changes made by the pipeline.

The final results showed:

- **4 datasets** with cleaning changes
- **14 total cleaning changes**

These numbers describe observed cleaning activity.

They should **not** be interpreted as an accuracy percentage because the benchmark does not contain a complete ground-truth record of every possible cleaning issue in every dataset.

Therefore, the benchmark does not claim:

> DataSense automatically fixed X% of all data-quality problems.

Instead, it reports how many cleaning changes were logged during the benchmark runs.

---

### 4.3 Insight Generation

Each dataset was evaluated to determine whether the analysis pipeline could produce a valid insight response.

The final results were:

| Result | Count |
|---|---:|
| Datasets evaluated | 15 |
| Valid insights | 14 |
| Insufficient datasets | 1 |
| Pipeline errors | 0 |

---

## 5. Insufficient-Data Dataset

One dataset, `events.csv`, was classified as insufficient for the current analysis pipeline.

The dataset contained event/timestamp information but did not provide a usable combination of business value and grouping information for the supported analyses.

This was treated as an expected analytical outcome rather than a pipeline failure.

Therefore:

```text
Insufficient data != pipeline error
```

This distinction is important when evaluating a system intended to handle arbitrary CSV files.

---

## 6. Pipeline Errors

The benchmark recorded:

```text
0 pipeline errors
```

A pipeline error means the software failed while processing a dataset rather than intentionally reporting that a particular analysis was unavailable.

The distinction is:

### Valid insufficient result

```text
Dataset processed successfully
        |
        v
Required analytical field unavailable
        |
        v
Analysis marked unavailable
```

### Pipeline error

```text
Dataset processing
        |
        v
Unexpected software failure
```

The benchmark counts these separately.

---

## 7. Runtime Measurement

Runtime was measured for the benchmark pipeline execution.

The final average runtime was:

```text
8.527 seconds
```

This should be understood as the average observed runtime across the benchmark pool and not as a guaranteed response time for every future CSV.

Runtime depends on factors including:

- dataset size
- number of columns
- parsing cost
- type inference
- cleaning
- aggregation
- available hardware
- filesystem performance

---

## 8. Large Dataset Coverage

The benchmark included datasets containing millions of rows.

This was important because DataSense is intended to work beyond small demonstration datasets.

Large files were useful for identifying:

- expensive inference operations
- inefficient full-column scans
- unnecessary repeated computation
- analysis bottlenecks

The pipeline was optimized where broad improvements were possible without introducing dataset-specific logic.

---

## 9. Benchmark Workflow

The benchmark workflow can be summarized as:

```text
Dataset
   |
   v
CSV Loading
   |
   v
Type Inference
   |
   v
Cleaning
   |
   v
Column Selection
   |
   v
Analysis
   |
   +--> Valid insights
   |
   +--> Insufficient data
   |
   +--> Pipeline error
   |
   v
Benchmark Metrics
```

The same general pipeline was used across the dataset pool.

---

## 10. Typing Accuracy Calculation

Typing accuracy was calculated as:

```text
correct type assignments
------------------------
evaluated type assignments
```

The final benchmark result was:

```text
140
---
158
```

Therefore:

```text
88.61%
```

This metric represents the evaluated typing cases in the benchmark.

It does not mean that every column in every possible CSV would achieve the same accuracy.

---

## 11. Remaining Typing Mismatches

The final benchmark still contained some mismatches.

Examples included:

### E-Commerce dataset

- `order_id`: identifier inferred as text
- `prod_sku`: identifier inferred as text

### Online shoppers dataset

- `Administrative_Duration`: decimal inferred as quantity
- `Informational_Duration`: decimal inferred as quantity
- `PageValues`: decimal inferred as quantity
- `SpecialDay`: decimal inferred as quantity
- `Revenue`: category inferred as text

### Orders dataset

- `eval_set`: category inferred as identifier
- `order_number`: quantity inferred as identifier
- `days_since_prior_order`: decimal inferred as quantity

### Stores dataset

- `AreaStore`: decimal inferred as quantity
- `Checkout Number`: quantity inferred as identifier

### Train dataset

- `Store`: identifier inferred as quantity
- `SchoolHoliday`: category inferred as quantity

### Transaction dataset

- `RETAIL_DISC`: currency inferred as decimal
- `WEEK_NO`: quantity inferred as identifier
- `COUPON_DISC`: currency inferred as quantity
- `COUPON_MATCH_DISC`: currency inferred as quantity

These mismatches were intentionally not all eliminated with dataset-specific rules.

---

## 12. Why the Benchmark Was Not Overfit

The remaining mismatches were reviewed after the general inference improvements.

The decision was made to stop at the final benchmark result rather than continuously adding special cases.

The reasoning was:

1. Some mismatches represent ambiguous semantic types.
2. A rule that fixes one dataset may harm another.
3. The goal is general-purpose CSV support.
4. Benchmark accuracy is only one part of system quality.
5. The system already processed all 15 datasets without pipeline errors.

This preserves a more general inference architecture.

---

## 13. Benchmark Artifacts

The benchmark produced supporting artifacts under:

```text
benchmarks/
```

including:

```text
run_benchmark.py
benchmark_results.json
benchmark_manifest.json
typing_mismatches.csv
results.md
```

These files provide reproducible benchmark information and allow future benchmark runs to be compared with the Phase 5 baseline.

---

## 14. Benchmark Limitations

The benchmark has several limitations.

### 14.1 Limited Dataset Count

The benchmark contains 15 datasets.

This is useful for validation but is not large enough to establish universal performance.

### 14.2 Type Ground Truth

The expected typing labels are benchmark-specific evaluation labels.

Real-world schemas can contain ambiguous columns where multiple interpretations are reasonable.

### 14.3 Cleaning Ground Truth

There is no complete independent ground truth for every possible data-quality problem.

Therefore, cleaning-change counts should not be interpreted as a percentage of all issues fixed.

### 14.4 Runtime Environment

Runtime depends on the machine and environment used for testing.

The reported average should therefore be treated as a benchmark baseline rather than a universal performance guarantee.

### 14.5 Domain Scope

The dataset pool focuses heavily on retail, e-commerce, and related business data.

Performance on unrelated domains has not been established by this benchmark.

---

## 15. How to Use This Benchmark

The Phase 5 benchmark should be treated as a baseline for future development.

Future changes should be evaluated against:

- typing accuracy
- valid insight generation
- insufficient-data handling
- pipeline errors
- runtime
- behavior on previously unseen schemas

A change should not be considered an improvement solely because one benchmark metric increases.

The broader question is whether the change makes DataSense more reliable on general CSV data.

---

## 16. Final Phase 5 Baseline

The final Phase 5 benchmark baseline is:

```text
Datasets evaluated:       15
Valid insights:            14
Insufficient datasets:      1
Pipeline errors:            0
Typing accuracy:      88.61%
Typing cases:          140 / 158
Cleaning datasets:           4
Cleaning changes:           14
Average runtime:        8.527 s
```

This baseline should be preserved so future optimization work can be compared against the same evaluation.

---

## 17. Interpretation

The benchmark demonstrates that the current DataSense pipeline can process a diverse set of retail/e-commerce CSV datasets and produce valid analytical outputs for most of the tested files without pipeline failures.

The results should be presented as a **Phase 5 engineering benchmark**, not as a universal claim about CSV-analysis accuracy.

The most important outcome is that the pipeline has a measurable baseline that can be used for future optimization and regression testing.
