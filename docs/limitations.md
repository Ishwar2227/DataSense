# DataSense — Limitations

## 1. Purpose

This document records the known limitations of the current DataSense implementation.

The purpose is to make the system's current boundaries explicit rather than presenting the prototype as more capable than it is.

---

## 2. CSV-Only Input

The current application is designed around CSV uploads.

Supported workflow:

```text
CSV upload
   |
   v
DataSense analysis
```

Other file formats are outside the current product scope.

Future versions may support additional tabular formats.

---

## 3. Heuristic Type Inference

DataSense uses heuristic-based type inference.

The system considers:

- column names
- sampled values
- numeric characteristics
- date parsing
- identifier patterns
- semantic hints

This approach works across varied schemas but cannot perfectly understand every possible column meaning.

Some columns may legitimately have ambiguous types.

---

## 4. Typing Is Not Perfect

The Phase 5 benchmark achieved:

```text
140 / 158
88.61%
```

typing accuracy across the evaluated cases.

Therefore, some type-inference mismatches remain.

Examples include columns where:

- a numeric field can reasonably be a quantity or identifier
- a numeric categorical field resembles a measurement
- a business metric has an ambiguous name
- a field's meaning depends on domain context

The benchmark result is a development baseline, not a universal accuracy guarantee.

---

## 5. Automatic Value Selection Can Be Imperfect

DataSense dynamically selects a business value column using semantic and data-quality signals.

However, datasets can contain multiple plausible value columns.

For example:

```text
Sales
Profit
Cost
Revenue
Freight
Tax
```

The current heuristic may not always select the metric a particular user considers most important.

This is a known limitation of automatic schema understanding.

---

## 6. Automatic Group Selection Can Be Imperfect

The system attempts to select useful categorical dimensions while avoiding identifier-like fields.

However, some datasets contain many valid grouping dimensions.

For example:

```text
Region
Category
Segment
Country
Customer Type
Product Type
```

The current selection logic chooses one suitable analytical group rather than understanding the user's complete business context.

---

## 7. Date-Based Analysis Requires a Usable Date Column

Time-based analysis requires a usable date column.

When no suitable date field exists:

- monthly trends are unavailable
- latest-vs-previous-period analysis is unavailable
- time-based contributor analysis is unavailable

This is expected behavior rather than a pipeline error.

---

## 8. Trend Analysis Is Monthly

The current trend analysis is based on monthly aggregation when suitable date data exists.

The system does not currently provide a fully configurable time-granularity system for:

- daily analysis
- weekly analysis
- quarterly analysis
- custom fiscal periods

These can be added in future versions.

---

## 9. Limited Question Intents

The current Ask Data feature supports a controlled set of question types.

The main supported intents are:

- why value/sales changed
- top group change
- anomaly questions

It does not yet provide unrestricted natural-language data analysis.

For unsupported questions, the system returns a safe fallback rather than pretending to perform an unsupported analysis.

---

## 10. No General Causal Analysis

A change in a business metric does not automatically reveal its cause.

For example:

```text
Sales decreased by 20%.
```

does not by itself prove:

```text
Customers preferred a competitor.
```

The current system reports observed statistics and does not invent causal explanations.

True causal analysis would require additional variables and analytical methods.

---

## 11. Anomaly Detection Is Simple

The current anomaly detection uses a z-score threshold:

```text
|Z| >= 3
```

This is intentionally simple and explainable.

However, z-score detection may not be appropriate for every distribution.

It can be affected by:

- skewed distributions
- heavy tails
- extreme values
- non-normal data
- seasonal patterns

More advanced anomaly-detection approaches can be considered later.

---

## 12. LLM Answers Depend on Available Statistics

The LLM does not receive unrestricted access to the dataset for every question.

Instead, the system provides question-specific trusted statistics.

This improves grounding but also limits the types of questions the LLM can answer.

If the required statistic is not available, the system should report that limitation.

---

## 13. LLM Does Not Establish Business Truth

The LLM is used to turn computed statistics into natural language.

It should not be treated as the source of truth for numerical analysis.

The deterministic analysis layer remains the source of:

- calculated values
- changes
- percentages
- group comparisons
- anomaly results

The generated response is therefore constrained by the statistics provided to the model.

---

## 14. Large Dataset Runtime

Large CSV files can take significant time to process.

Runtime depends on:

- number of rows
- number of columns
- parsing cost
- type inference
- cleaning
- aggregation
- available hardware

The Phase 5 benchmark reported an average runtime of:

```text
8.527 seconds
```

This is a benchmark baseline, not a guaranteed runtime for every dataset.

---

## 15. Memory and Resource Requirements

Large datasets require additional memory and processing resources.

DataSense currently uses pandas-based processing.

Very large CSV files may therefore require substantial system memory.

The application is not yet designed as a distributed big-data processing system.

---

## 16. Benchmark Scope Is Limited

The Phase 5 benchmark evaluated:

```text
15 datasets
```

The datasets were primarily retail, e-commerce, and related business datasets.

The benchmark therefore does not establish performance across every possible CSV domain.

Results should be interpreted within the tested scope.

---

## 17. Cleaning Does Not Mean Perfect Data Repair

The cleaning layer performs supported transformations such as:

- encoding handling
- type normalization
- date parsing
- numeric normalization
- category normalization

It does not guarantee that every data-quality issue is detected or corrected.

In particular, semantic business errors can be difficult to identify automatically.

For example, the system cannot reliably determine from values alone whether:

```text
Revenue = 100000
```

is genuinely correct for a particular business.

---

## 18. No Complete Data Lineage System

The current application reports cleaning and analysis information but is not a full enterprise data-lineage platform.

It does not currently provide complete lineage tracking across:

- source systems
- transformations
- downstream reports
- historical versions
- external databases

This may be added as the product evolves.

---

## 19. No Authentication or Multi-User System Yet

The current application is primarily designed as a single-user analytical prototype.

Enterprise features such as:

- authentication
- user accounts
- role-based access
- organization management
- team workspaces

are outside the current implementation scope.

---

## 20. No Persistent Production Data Store

The current workflow centers on uploaded CSV files and in-memory/local processing.

A production version may require:

- persistent dataset storage
- database-backed metadata
- dataset versioning
- user-specific history
- access controls

These are not part of the current core analysis pipeline.

---

## 21. LLM API Dependency

The natural-language Ask Data experience depends on the configured LLM provider.

If the required API configuration is unavailable or the provider cannot be reached, LLM-generated responses cannot be produced.

The deterministic analysis layer remains conceptually separate from this dependency.

---

## 22. API and Deployment Security Still Need Production Hardening

The development architecture keeps LLM credentials on the backend.

However, a production deployment requires additional security review, including:

- authentication
- request validation
- rate limiting
- upload restrictions
- resource limits
- logging
- secret management
- abuse prevention
- secure CORS configuration

These are deployment-hardening concerns rather than core analysis logic.

---

## 23. No Guaranteed Business Interpretation

DataSense can identify statistical changes, but it cannot automatically understand every business context.

For example, a revenue change may be influenced by:

- pricing
- promotions
- inventory
- customer behavior
- seasonality
- operational changes

unless the dataset contains information that allows those factors to be analyzed.

The current system should therefore be treated as a data-analysis assistant, not an autonomous business decision-maker.

---

## 24. Current Product Boundary

The current DataSense system is best described as:

> A CSV-based analytical assistant that automatically profiles, cleans, analyzes, and explains supported business data using deterministic statistics and grounded LLM responses.

It is not currently:

- a universal data scientist
- a complete BI replacement
- a causal inference engine
- a distributed big-data platform
- an enterprise data-governance system
- an unrestricted autonomous analytics agent

These distinctions should remain clear in the README, documentation, and demo.

---

## 25. Future Improvements

Potential future improvements include:

- broader file-format support
- stronger semantic type inference
- user-selectable value and group columns
- configurable time granularity
- richer anomaly detection
- more analytical question intents
- open-ended analytical querying
- causal-analysis workflows
- persistent datasets
- user accounts
- authentication and authorization
- production monitoring
- stronger security controls
- larger benchmark suites
- further performance optimization

These are future directions rather than current capabilities.
