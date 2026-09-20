# DataSense — Cleaning Rules

## 1. Purpose

Define how DataSense cleans, standardizes, and prepares uploaded
datasets before analysis.

The cleaning pipeline is designed to make common transformations
automatic while preserving genuine missing or uncertain values.

---

## 2. Encoding Detection

DataSense attempts to read uploaded CSV files using:

1. UTF-8
2. Automatic encoding detection when UTF-8 fails
3. `latin-1` as a fallback when necessary

Encoding-related transformations or fallback decisions are recorded
in the cleaning report when applicable.

---

## 3. Column Type Detection

DataSense automatically classifies columns as:

- `date`
- `id`
- `currency`
- `quantity`
- `decimal`
- `category`
- `text`

Type inference uses both:

- sampled data values
- column-name semantics

Values are the primary evidence, while column names provide
additional semantic hints.

Only a small representative sample is inspected rather than
scanning every value solely for type inference.

---

## 4. Date Detection

DataSense recognizes common date formats such as:

- `2024-01-31`
- `2024-01-31 15:41`
- `2024/01/31`
- `2005-03`
- `31-12-2023`
- `31/12/2023`

A column is classified as a date when a sufficiently large proportion
of sampled values match supported date patterns and can be parsed.

Explicit date-name hints include:

- date
- timestamp
- datetime

Generic `time` or `year` alone is **not automatically treated as a date**.

This distinction was introduced to avoid incorrectly classifying
time-of-day or year-number columns as dates.

---

## 5. Identifier Detection

DataSense can identify identifier-like columns using both semantic
names and value shapes.

Common identifier hints include:

- ID
- code
- number
- invoice ID
- order ID
- customer ID
- product ID
- item ID
- transaction ID
- visitor ID
- household key
- basket ID
- store ID
- postal code
- postcode
- ZIP
- census tract

Common concatenated identifier names such as:

- `visitorid`
- `itemid`
- `transactionid`

are also recognized.

Identifier detection occurs before generic quantity detection so that
numeric IDs are not incorrectly interpreted as measurements.

---

## 6. Currency Detection and Normalization

Currency detection recognizes explicit currency symbols such as:

- `$`
- `₹`
- `€`
- `£`

Column-name semantics can also identify plain numeric monetary fields
such as:

- sales
- revenue
- price
- profit
- cost
- amount
- total
- income
- expense
- fee
- MRP
- freight
- COGS

Currency values can be normalized into numeric values for analysis.

Invalid numeric conversions become missing values rather than being
silently replaced with invented values.

---

## 7. Quantity Detection

Integer-like numeric columns can be classified as `quantity`.

Examples include:

- product quantity
- order quantity
- number of items
- counts

However, a numeric column is not automatically considered a quantity
when its name strongly indicates another semantic type such as:

- ID
- currency
- category

This prevents numeric identifiers and numeric categorical fields from
being treated as measurements.

---

## 8. Decimal Detection

Decimal-like numeric columns are classified separately from integer
quantities.

Common semantic hints include:

- discount
- rate
- percent
- percentage
- ratio
- margin
- score
- rating
- viewership
- duration

Decimal fields may represent measurements, rates, percentages,
scores, or other continuous values.

---

## 9. Numeric Categorical Fields

Some datasets represent categories using numbers.

Examples include:

- `Open` → 0/1
- `Promo` → 0/1
- `StateHoliday` → encoded categories

A strong categorical column-name hint can therefore classify a
numeric column as `category`.

Generic numeric columns with a small number of unique values are not
automatically treated as categories.

This prevents fields such as `Quantity` or shipping-day measurements
from being incorrectly classified merely because the first sampled
values contain only a few unique numbers.

---

## 10. Column Name Hints

Column names provide secondary semantic evidence.

Examples:

### Identifier hints

```text
id
code
number
order id
product id
visitorid
```

### Date hints
date
timestamp
datetime

### Currency hints
price
sales
profit
cost
amount
revenue
total
income

### Decimal hints
discount
rate
percent
ratio
margin
rating
duration

### Category hints
category
type
segment
region
country
city
state
status
gender
group
market
branch
property
promo
Name hints are deliberately treated as semantic evidence rather than
blind overrides.

## 11. Category Normalization
Categorical values may be normalized by:
- trimming surrounding whitespace
- standardizing representations
- matching highly similar values when appropriate
The goal is to reduce accidental category duplication while
preserving genuine distinct values.

## 12. Fuzzy Matching Performance Rule
Fuzzy matching is not applied indiscriminately.
For high-cardinality columns, fuzzy matching can become expensive and
can also produce unreliable matches.
Current rule:
```bash
> 300 unique values → skip fuzzy matching
```
This keeps cleaning practical for large datasets.

## 13. Missing and Invalid Values
DataSense attempts to preserve genuine missing values.
Examples:
- empty values remain missing
- failed numeric conversions become NaN
- invalid dates remain invalid rather than being fabricated
Cleaning should not silently invent information that was not present
in the uploaded dataset.

## 14. Cleaning Log
Important transformations are recorded in the cleaning report.
The report helps users understand:
- what DataSense changed
- which columns were affected
- what kind of cleaning occurred
The benchmark records observed cleaning changes, but these counts do
not represent a complete ground-truth measurement of every possible
data-quality problem in a dataset.

## 15. Performance Considerations
DataSense avoids unnecessary full-column operations where possible.
Type inference uses small samples, and representative samples are
used by analysis-column selection.
This is important because DataSense is intended to work with large
CSV files.

## 16. Limitations
Automatic cleaning and type inference are heuristic.
Potential uncertainty remains when:
- a column name is ambiguous
- numeric values can represent multiple concepts
- identifiers resemble quantities
- categories are encoded numerically
- a dataset contains unusual date formats
- business meaning cannot be inferred from the CSV alone
DataSense therefore favors conservative behavior and reports
uncertainty rather than silently inventing business meaning.