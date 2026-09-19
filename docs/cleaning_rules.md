# DataSense — Cleaning Rules

## 1. Purpose
Explain that this document defines the rules used to clean,
standardize, and prepare uploaded datasets before analysis.

## 2. Encoding Detection
- Try UTF-8 first.
- If UTF-8 fails, detect the encoding automatically.
- Use the detected encoding.
- Fall back to latin-1 if necessary.
- Record encoding changes in the cleaning log.

## 3. Column Type Detection
Automatically classify columns as:
- date
- id
- currency
- quantity
- decimal
- category
- text

## 4. Date Detection
- Detect common date formats.
- Identify a column as date when the majority of sampled
  values match supported date patterns.

## 5. ID Detection
- High-cardinality columns containing numeric/code-like values
  can be classified as IDs.
- ID detection occurs before quantity detection.

## 6. Currency Detection & Normalization
- Recognize currency symbols and money-like decimal values.
- Remove currency symbols and separators.
- Convert valid values to numeric values.
- Invalid conversions become NaN.
- Record failed conversions.

## 7. Quantity Detection
- Plain integer values are treated as quantities when they
  are not identified as IDs or currency.

## 8. Decimal Detection
- Decimal values are detected separately from integer quantities.
- Decimal-like columns can represent rates, percentages,
  margins, etc.

## 9. Column Name Hints
Column names can improve type detection.

Examples:
- ID/code/number → id
- date/time → date
- price/sales/profit/cost/amount/revenue → currency
- discount/rate/percent/ratio/margin → decimal

## 10. Category Normalization
- Trim whitespace.
- Normalize category capitalization.
- Merge highly similar values when appropriate.

## 11. Fuzzy Matching Performance Rule
- Fuzzy matching is skipped for high-cardinality columns.
- Current threshold: more than 300 unique values.
- Reason: fuzzy matching can become expensive as unique values increase.

## 12. Missing and Invalid Values
- Preserve genuine missing values where possible.
- Invalid numeric conversions become NaN.
- Cleaning should not silently invent values.

## 13. Cleaning Log
Every important transformation should be recorded so the
user can understand what DataSense changed.

## 14. Limitations
Document cases where automatic cleaning may be uncertain,
especially ambiguous column types and high-cardinality text columns.