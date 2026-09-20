# DataSense — Architecture

## 1. Overview

DataSense is a full-stack data analysis application that accepts CSV
files, cleans and profiles them, automatically selects meaningful
analysis columns, generates statistical insights, and provides
grounded natural-language answers to supported business questions.

The system is divided into two main applications:

- React/Vite frontend
- FastAPI backend

The backend owns data processing and analysis. The frontend is
responsible for presentation and user interaction.

---

## 2. High-Level Architecture

```text
User
  │
  ▼
React / Vite Frontend
  │
  │ HTTP requests
  ▼
FastAPI Backend
  │
  ├── Upload API
  │
  ├── Cleaning Pipeline
  │     ├── Encoding detection
  │     ├── Type inference
  │     ├── Date normalization
  │     ├── Currency normalization
  │     └── Category matching
  │
  ├── Analysis Pipeline
  │     ├── Column selection
  │     ├── Trend analysis
  │     ├── Change detection
  │     └── Anomaly detection
  │
  └── Question API
        ├── Intent detection
        ├── Trusted question statistics
        ├── Question cache
        └── Groq LLM
```

## 3. Frontend
### The frontend is implemented using:
- React
- Vite
- CSS
### The frontend provides:
- CSV upload
- Dataset status
- Cleaning report
- Selected analysis columns
- Trend visualization
- Top contributor analysis
- Outlier analysis
- Data preview
- Ask Data interface
- Loading states
- Error states
- Insufficient-data states
The frontend does not independently calculate the business
statistics used in the dashboard.
Instead, it consumes structured results from the backend API.
This keeps the analysis logic centralized and prevents the frontend
and backend from producing different interpretations of the same
dataset.

## 4. Backend
The backend uses:
- Python
- FastAPI
- Pandas
- Pydantic
- Uvicorn
FastAPI exposes the application APIs and coordinates the processing
pipeline.
### The backend is responsible for:
1. Receiving uploaded CSV files.
2. Reading the data safely.
3. Cleaning and normalizing the dataset.
4. Inferring column types.
5. Selecting analysis columns.
6. Building statistical insights.
7. Preparing structured statistics for supported questions.
8. Generating grounded natural-language answers.

## 5. Cleaning Layer
The cleaning layer prepares uploaded data for analysis.
### Important components include:
```text
backend/app/cleaning/
├── pipeline.py
├── type_inference.py
├── date_normalizer.py
├── currency_normalizer.py
└── category_matcher.py
```
The cleaning layer is deliberately separated from analysis so that
analysis operates on a normalized representation of the dataset.
The cleaning pipeline also produces information used by the
cleaning report shown in the frontend.

## 6. Analysis Layer
The analysis layer contains the business-analysis logic.
### Important components include:
```text
backend/app/analysis/
├── column_selector.py
├── insights_builder.py
├── trends.py
├── change_detection.py
└── anomaly_detection.py
```
### Column selection
column_selector.py dynamically selects:
- date column
- value column
- group column
The selector uses semantic column names, inferred types, cardinality,
numeric coverage, variation, and identifier exclusion rules.

## 7. Trend Analysis
Trend analysis converts the selected date column into monthly
periods and aggregates the selected value.
The result is a chronological monthly series that can be displayed by
the frontend.
### Trend analysis requires:
- a usable date column
- a usable value column
If either is unavailable, the frontend reports that the trend cannot
be calculated.

## 8. Change Detection
When at least two time periods are available, DataSense compares:
- latest available period
- previous available period
It calculates:
- absolute change
- percentage change
These statistics are also used by the supported "why did the value
change?" question.

## 9. Contributor Analysis
When a group column is available in addition to date and value
columns, DataSense compares group-level values between the latest and
previous periods.
This allows DataSense to identify which group changed the most.
The system reports the observed change but does not claim that the
group caused the change.

## 10. Anomaly Detection
DataSense uses Z-score based anomaly detection.
Current threshold:
```bash
|Z-score| >= 3.0
```
The result identifies unusually large or small observations.
An anomaly is treated as a statistical observation, not automatically
as a data error or business problem.

## 11. Question Answering Architecture
DataSense does not send unrestricted raw-data questions directly to
the language model.
The question-answering flow is:
```text
User question
     │
     ▼
Question intent detection
     │
     ▼
Supported analysis intent
     │
     ▼
Trusted statistics from analysis
     │
     ▼
Grounded prompt
     │
     ▼
Groq LLM
     │
     ▼
Natural-language answer
```
Current supported intents include:
- why_change
- top_group
- anomalies
Unsupported questions receive a safe fallback instead of causing the
LLM to invent an answer.

## 12. LLM Grounding
The language model is instructed to use only the trusted statistics
provided by DataSense.
The model is explicitly instructed not to:
- invent numbers
- invent causes
- invent events
- make unsupported calculations
- claim that the available data explains something when it does not
This design separates:
- statistical computation → deterministic backend
- natural-language explanation → LLM
This is an important architectural boundary.

## 13. Question Cache
Repeated questions can use cached results rather than repeating the
same expensive processing.
The cache is associated with the dataset/question context so that
answers from one dataset are not incorrectly reused for another.
Caching was introduced to reduce repeated question latency,
especially for larger datasets.

## 14. API Boundary
The frontend communicates with the backend through HTTP APIs.
The main responsibilities are separated into endpoints for:
- file upload and analysis
- insights
- questions
The frontend receives structured JSON and renders the result.
This allows the frontend and backend to be developed and deployed
independently.

## 15. Why DataSense Uses a Heuristic Pipeline
DataSense is designed to work with previously unseen CSV schemas.
A fixed schema would make the system reliable only for a small number
of known datasets.
Instead, DataSense combines:
- value-based inference
- semantic column-name hints
- cardinality
- numeric characteristics
- identifier detection
- business-oriented scoring
This allows the same pipeline to operate across different retail
and e-commerce datasets.

## 16. Failure Handling
DataSense is designed to fail explicitly rather than fabricate
results.
Examples:
- Missing value column → value-based analysis unavailable
- Missing date column → trend/change analysis unavailable
- Missing group column → contributor analysis unavailable
- Unsupported question → safe question-answer fallback
- Insufficient data → explicit insufficient-data state
- Invalid numeric conversion → missing value rather than invented data
The frontend exposes these states to the user rather than displaying
misleading empty charts or fabricated conclusions.

## 17. Performance Design
Several design decisions were made specifically for larger CSV files:
- Type inference uses small samples.
- Column selection uses representative samples.
- Expensive fuzzy matching is skipped for high-cardinality columns.
- Pandas operations are used for vectorized transformations.
- Repeated question results can be cached.
The Phase 5 benchmark measured an average runtime of approximately
8.527 seconds per dataset across the benchmark collection.

## 18. Deployment Architecture
The planned production architecture separates the frontend and
backend:
```text
User
 │
 ▼
Vercel
React / Vite frontend
 │
 │ HTTPS API requests
 ▼
Render
FastAPI backend
 │
 ├── Data processing
 ├── Analysis
 └── Groq API
```
The frontend and backend therefore have independent deployment
lifecycles.
Secrets such as the Groq API key remain on the backend and are not
embedded in the frontend.

## 19. Security and Secrets
API credentials are stored through environment variables.
The local .env file is excluded from Git.
Secrets must never be:
- committed to GitHub
- placed in frontend source code
- included in benchmark artifacts
- displayed in application responses
Production secrets should be configured through the deployment
platform's environment-variable settings.

## 20. Architectural Limitations
The architecture currently assumes:
- CSV as the primary input format
- a single uploaded dataset per analysis workflow
- heuristic semantic interpretation
- statistical rather than causal analysis
- supported question intents rather than unrestricted analytical
  reasoning
These constraints are deliberate for the current project scope.