import json
import sys
import time
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

BENCHMARK_DIR = ROOT / "benchmarks"
DATASET_DIR = ROOT / "sample_db" / "benchmark_datasets"
MANIFEST_PATH = BENCHMARK_DIR / "benchmark_manifest.json"
RESULTS_PATH = BENCHMARK_DIR / "benchmark_results.json"


# ---------------------------------------------------------------------------
# Make backend imports available
# ---------------------------------------------------------------------------

BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app.cleaning.pipeline import clean_dataframe
from app.analysis.insights_builder import build_insights
from app.api.upload import read_csv_safely


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CSV_CHUNK_SIZE = 100_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_manifest():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def file_size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 2)


def count_rows(path: Path) -> int:
    """
    Count CSV data rows without loading the entire file into pandas.

    This is only used for reporting.
    """
    with open(path, "rb") as f:
        return max(sum(1 for _ in f) - 1, 0)


def load_csv(path: Path):
    """
    Read the CSV using DataSense's own safe CSV reader.

    The benchmark therefore tests the same parsing approach
    used by the application.
    """
    with open(path, "rb") as f:
        contents = f.read()

    df, encoding_log = read_csv_safely(contents)

    return df, encoding_log


def calculate_type_accuracy(
    detected_types: dict,
    expected_types: dict
):
    """
    Compare only the columns explicitly defined in the benchmark manifest.

    This prevents the benchmark from pretending that every column
    has an unquestionable ground-truth semantic type.
    """

    comparisons = []

    correct = 0
    total = 0

    for column, expected in expected_types.items():

        detected = detected_types.get(column)

        if detected is None:
            status = "missing"
        elif detected == expected:
            status = "correct"
            correct += 1
        else:
            status = "incorrect"

        total += 1

        comparisons.append({
            "column": column,
            "expected": expected,
            "detected": detected,
            "status": status
        })

    accuracy = (
        round((correct / total) * 100, 2)
        if total
        else None
    )

    return {
        "correct": correct,
        "total": total,
        "accuracy_pct": accuracy,
        "comparisons": comparisons
    }


def determine_insight_status(insights: dict):
    """
    Classify the result without treating legitimately unavailable
    analyses as pipeline failures.
    """

    if not isinstance(insights, dict):
        return "pipeline_error"

    if "error" in insights:
        return "insufficient_data"

    selected = insights.get("selected_columns", {})

    value_column = selected.get("value_col")

    if not value_column:
        return "insufficient_data"

    question_stats = insights.get("question_stats", {})

    available_questions = sum(
        1
        for stat in question_stats.values()
        if isinstance(stat, dict)
        and stat.get("available") is True
    )

    if available_questions > 0:
        return "valid"

    return "insufficient_data"


def get_question_availability(insights: dict):
    stats = insights.get("question_stats", {})

    result = {}

    for question_id in [
        "why_change",
        "top_group",
        "anomalies"
    ]:

        question = stats.get(question_id, {})

        result[question_id] = bool(
            isinstance(question, dict)
            and question.get("available") is True
        )

    return result


def run_dataset(path: Path, expected_types: dict):

    print()
    print("=" * 80)
    print(f"DATASET: {path.name}")
    print("=" * 80)

    dataset_start = time.perf_counter()

    result = {
        "dataset": path.name,
        "rows": None,
        "columns": None,
        "file_size_mb": file_size_mb(path),
        "runtime_seconds": None,
        "status": None,
        "error": None,
        "encoding_log": [],
        "cleaning_changes": [],
        "cleaning_change_count": 0,
        "detected_types": {},
        "typing": {},
        "selected_columns": {},
        "question_availability": {},
        "unavailable_analyses": []
    }

    try:

        # ---------------------------------------------------------------
        # 1. Load CSV using DataSense's parser
        # ---------------------------------------------------------------

        load_start = time.perf_counter()

        df, encoding_log = load_csv(path)

        load_time = time.perf_counter() - load_start

        result["rows"] = len(df)
        result["columns"] = len(df.columns)
        result["encoding_log"] = encoding_log

        print(
            f"Loaded: {len(df):,} rows × {len(df.columns)} columns "
            f"in {load_time:.2f}s"
        )

        # ---------------------------------------------------------------
        # 2. Cleaning
        # ---------------------------------------------------------------

        cleaning_start = time.perf_counter()

        cleaned_df, cleaning_report = clean_dataframe(df)

        cleaning_time = time.perf_counter() - cleaning_start

        detected_types = cleaning_report.get(
            "column_types",
            {}
        )

        cleaning_changes = cleaning_report.get(
            "changes",
            []
        )

        result["detected_types"] = detected_types
        result["cleaning_changes"] = cleaning_changes
        result["cleaning_change_count"] = len(
            cleaning_changes
        )

        print(
            f"Cleaning: {cleaning_time:.2f}s | "
            f"changes logged: {len(cleaning_changes)}"
        )

        # ---------------------------------------------------------------
        # 3. Type accuracy
        # ---------------------------------------------------------------

        typing = calculate_type_accuracy(
            detected_types,
            expected_types
        )

        result["typing"] = typing

        print(
            f"Typing accuracy: "
            f"{typing['correct']}/{typing['total']} "
            f"({typing['accuracy_pct']}%)"
        )

        # ---------------------------------------------------------------
        # 4. Insights
        # ---------------------------------------------------------------

        insight_start = time.perf_counter()

        insights = build_insights(
            cleaned_df,
            detected_types
        )

        insight_time = time.perf_counter() - insight_start

        result["selected_columns"] = insights.get(
            "selected_columns",
            {}
        )

        result["question_availability"] = (
            get_question_availability(insights)
        )

        result["unavailable_analyses"] = insights.get(
            "unavailable_analyses",
            []
        )

        result["status"] = determine_insight_status(
            insights
        )

        print(
            f"Insights: {insight_time:.2f}s"
        )

        print(
            f"Selected columns: "
            f"{result['selected_columns']}"
        )

        print(
            f"Question availability: "
            f"{result['question_availability']}"
        )

        print(
            f"Status: {result['status']}"
        )

    except Exception as exc:

        result["status"] = "pipeline_error"
        result["error"] = (
            f"{type(exc).__name__}: {exc}"
        )

        print(
            f"ERROR: {result['error']}"
        )

    finally:

        result["runtime_seconds"] = round(
            time.perf_counter() - dataset_start,
            3
        )

        print(
            f"Total runtime: "
            f"{result['runtime_seconds']:.3f}s"
        )

    return result


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def build_summary(results):

    total = len(results)

    valid = sum(
        r["status"] == "valid"
        for r in results
    )

    insufficient = sum(
        r["status"] == "insufficient_data"
        for r in results
    )

    errors = sum(
        r["status"] == "pipeline_error"
        for r in results
    )

    typing_totals = [
        r["typing"]
        for r in results
        if r["typing"].get("total", 0) > 0
    ]

    typing_correct = sum(
        t["correct"]
        for t in typing_totals
    )

    typing_total = sum(
        t["total"]
        for t in typing_totals
    )

    overall_typing_accuracy = (
        round(
            (typing_correct / typing_total) * 100,
            2
        )
        if typing_total
        else None
    )

    datasets_with_cleaning_changes = sum(
        r["cleaning_change_count"] > 0
        for r in results
    )

    total_cleaning_changes = sum(
        r["cleaning_change_count"]
        for r in results
    )

    avg_runtime = (
        round(
            sum(r["runtime_seconds"] for r in results)
            / total,
            3
        )
        if total
        else None
    )

    return {
        "datasets_evaluated": total,
        "valid_insights": valid,
        "insufficient_data": insufficient,
        "pipeline_errors": errors,
        "typing_correct": typing_correct,
        "typing_total": typing_total,
        "overall_typing_accuracy_pct": overall_typing_accuracy,
        "datasets_with_cleaning_changes": (
            datasets_with_cleaning_changes
        ),
        "total_cleaning_changes_logged": (
            total_cleaning_changes
        ),
        "average_runtime_seconds": avg_runtime
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    print()
    print("=" * 80)
    print("DATASENSE BENCHMARK")
    print("=" * 80)

    manifest = load_manifest()

    datasets_manifest = manifest.get(
        "datasets",
        {}
    )

    results = []

    dataset_files = sorted(
        DATASET_DIR.glob("*.csv")
    )

    print(
        f"Benchmark datasets found: "
        f"{len(dataset_files)}"
    )

    print(
        f"Manifest datasets: "
        f"{len(datasets_manifest)}"
    )

    missing_manifest = [
        path.name
        for path in dataset_files
        if path.name not in datasets_manifest
    ]

    if missing_manifest:

        print()
        print(
            "WARNING: These datasets are not in the manifest:"
        )

        for name in missing_manifest:
            print(f"  - {name}")

    print()

    # ---------------------------------------------------------------
    # Run each dataset
    # ---------------------------------------------------------------

    for path in dataset_files:

        dataset_config = datasets_manifest.get(
            path.name,
            {}
        )

        expected_types = dataset_config.get(
            "expected_types",
            {}
        )

        result = run_dataset(
            path,
            expected_types
        )

        results.append(result)

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------

    summary = build_summary(
        results
    )

    output = {
        "benchmark": "DataSense Phase 5",
        "datasets": results,
        "summary": summary
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ---------------------------------------------------------------
    # Print final summary
    # ---------------------------------------------------------------

    print()
    print()
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    print(
        f"Datasets evaluated:       "
        f"{summary['datasets_evaluated']}"
    )

    print(
        f"Valid insights:            "
        f"{summary['valid_insights']}"
    )

    print(
        f"Insufficient data:         "
        f"{summary['insufficient_data']}"
    )

    print(
        f"Pipeline errors:           "
        f"{summary['pipeline_errors']}"
    )

    print(
        f"Typing accuracy:           "
        f"{summary['typing_correct']}/"
        f"{summary['typing_total']} "
        f"({summary['overall_typing_accuracy_pct']}%)"
    )

    print(
        f"Datasets with cleaning "
        f"changes logged:           "
        f"{summary['datasets_with_cleaning_changes']}"
    )

    print(
        f"Total cleaning changes:    "
        f"{summary['total_cleaning_changes_logged']}"
    )

    print(
        f"Average runtime:           "
        f"{summary['average_runtime_seconds']}s"
    )

    print()
    print(
        f"Detailed results saved to:"
    )
    print(
        f"  {RESULTS_PATH}"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
