import pandas as pd
import math

from app.analysis.trends import compute_monthly_trend
from app.analysis.change_detection import find_top_contributors
from app.analysis.anomaly_detection import detect_outliers
from app.analysis.column_selector import select_analysis_columns


def sanitize_for_json(obj):
    """
    Recursively replaces NaN/inf values with None so that
    FastAPI can safely serialize the response as JSON.
    """

    if isinstance(obj, dict):
        return {
            k: sanitize_for_json(v)
            for k, v in obj.items()
        }

    elif isinstance(obj, list):
        return [
            sanitize_for_json(v)
            for v in obj
        ]

    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None

        return obj

    return obj


def build_insights(
    df: pd.DataFrame,
    column_types: dict
) -> dict:

    # =========================================================
    # WORK ON A COPY
    # =========================================================

    df = df.copy()
    column_types = column_types.copy()

    # =========================================================
    # DERIVED BUSINESS VALUE
    # =========================================================
    #
    # Prefer an existing business metric such as:
    #
    # Sales
    # Revenue
    # Amount
    # Total
    #
    # Otherwise try:
    #
    # Quantity × UnitPrice
    #
    # =========================================================

    value_candidates = [
        col
        for col in column_types
        if any(
            keyword in col.lower().replace(" ", "_")
            for keyword in [
                "sales",
                "revenue",
                "amount",
                "total",
                "net",
                "gross",
                "turnover"
            ]
        )
    ]

    # ---------------------------------------------------------
    # Create AnalysisValue only when necessary
    # ---------------------------------------------------------

    if not value_candidates:

        quantity_cols = [
            col
            for col in column_types
            if "quantity" in col.lower()
        ]

        price_cols = [
            col
            for col, t in column_types.items()
            if t == "currency"
            and any(
                keyword in col.lower().replace(" ", "_")
                for keyword in [
                    "unitprice",
                    "unit_price",
                    "price"
                ]
            )
        ]

        if quantity_cols and price_cols:

            quantity_col = quantity_cols[0]
            price_col = price_cols[0]

            quantity = pd.to_numeric(
                df[quantity_col],
                errors="coerce"
            )

            price = pd.to_numeric(
                df[price_col],
                errors="coerce"
            )

            df["AnalysisValue"] = quantity * price

            column_types["AnalysisValue"] = "currency"

    # =========================================================
    # SELECT ANALYSIS COLUMNS
    # =========================================================

    selected = select_analysis_columns(
        df,
        column_types
    )

    date_col = selected.get("date_col")
    value_col = selected.get("value_col")
    group_col = selected.get("group_col")

    # =========================================================
    # NO VALUE COLUMN
    # =========================================================

    if not value_col:

        return sanitize_for_json({
            "error": "Could not find a suitable numeric value column for analysis",

            "selected_columns": selected,

            "trend": [],

            "latest_month": None,

            "previous_month": None,

            "top_contributors": [],

            "outlier_count": 0,

            "outliers": [],

            # -------------------------------------------------
            # PHASE 4
            # No value means none of the quantitative
            # question templates can be answered safely.
            # -------------------------------------------------

            "question_stats": {
                "why_change": {
                    "available": False,
                    "reason": "Not enough data: no suitable value column was found."
                },

                "top_group": {
                    "available": False,
                    "reason": "Not enough data: no suitable value column was found."
                },

                "anomalies": {
                    "available": False,
                    "reason": "Not enough data: no suitable value column was found."
                }
            }
        })

    # =========================================================
    # TREND ANALYSIS
    # =========================================================

    trend_records = []

    latest_month = None
    previous_month = None

    if date_col:

        try:

            trend = compute_monthly_trend(
                df,
                date_col,
                value_col
            )

            if trend is not None and not trend.empty:

                trend_records = trend.to_dict(
                    orient="records"
                )

                months = trend["month"].tolist()

                if len(months) >= 1:
                    latest_month = months[-1]

                if len(months) >= 2:
                    previous_month = months[-2]

        except Exception:

            trend_records = []

            latest_month = None

            previous_month = None

    # =========================================================
    # TOP CONTRIBUTORS
    # =========================================================

    top_contributors = []

    if (
        date_col
        and group_col
        and latest_month
        and previous_month
    ):

        try:

            top_contributors = find_top_contributors(
                df,
                date_col,
                value_col,
                group_col,
                latest_month,
                previous_month
            )

        except Exception:

            top_contributors = []

    # =========================================================
    # OUTLIER DETECTION
    # =========================================================

    outliers = []

    try:

        outliers = detect_outliers(
            df,
            value_col,
            threshold=3.0
        )

    except Exception:

        outliers = []

    # =========================================================
    # RESULT
    # =========================================================

    result = {

        "selected_columns": selected,

        "trend": trend_records,

        "latest_month": latest_month,

        "previous_month": previous_month,

        "top_contributors": top_contributors,

        "outlier_count": len(outliers),

        "outliers": outliers[:20]
    }

    # =========================================================
    # PHASE 4 — QUESTION STATISTICS
    # =========================================================
    #
    # IMPORTANT:
    #
    # These are NOT LLM answers.
    #
    # These are the trusted numerical facts that will later
    # be passed to the LLM for plain-English phrasing.
    #
    # The LLM will NEVER analyze the complete CSV.
    #
    # =========================================================

    question_stats = {}

        # =========================================================
    # QUESTION 1
    #
    # "Why did the value change?"
    #
    # Requires:
    #
    # date + value + at least 2 months
    # =========================================================

    if (
        date_col
        and latest_month is not None
        and previous_month is not None
        and len(trend_records) >= 2
    ):

        latest_record = trend_records[-1]
        previous_record = trend_records[-2]

        # The trend dataframe stores the value using the
        # actual detected value-column name, such as:
        #
        # Sales
        # Revenue
        # AnalysisValue
        #
        latest_value = latest_record.get(value_col)
        previous_value = previous_record.get(value_col)

        change = None
        change_pct = None

        if (
            latest_value is not None
            and previous_value is not None
        ):

            try:

                latest_value = float(latest_value)
                previous_value = float(previous_value)

                change = latest_value - previous_value

                if previous_value != 0:
                    change_pct = (
                        change / previous_value
                    ) * 100

            except (TypeError, ValueError):

                change = None
                change_pct = None

        if change is not None:

            question_stats["why_change"] = {

                "available": True,

                "date_column": date_col,

                "value_column": value_col,

                "latest_month": latest_month,

                "previous_month": previous_month,

                "latest_value": latest_value,

                "previous_value": previous_value,

                "change": change,

                "change_pct": change_pct
            }

        else:

            question_stats["why_change"] = {

                "available": False,

                "reason": (
                    "Not enough reliable numerical data "
                    "to calculate the value change."
                )
            }

    else:

        question_stats["why_change"] = {

            "available": False,

            "reason": (
                "Not enough data: value-change analysis "
                "requires a date column and at least two "
                "time periods."
            )
        }

        # =========================================================
    # QUESTION 2
    #
    # "Which group changed the most?"
    #
    # Requires:
    #
    # date + value + group + two periods
    # =========================================================

    if (
        date_col
        and group_col
        and latest_month is not None
        and previous_month is not None
        and top_contributors
    ):

        # find_top_contributors() returns the group using
        # the actual detected group-column name.
        #
        # Example:
        #
        # group_col = "Region"
        #
        # result:
        #
        # {
        #     "Region": "West",
        #     "change": ...,
        #     "change_pct": ...
        # }

        top_group = top_contributors[0]

        question_stats["top_group"] = {

            "available": True,

            "group_column": group_col,

            "value_column": value_col,

            "latest_month": latest_month,

            "previous_month": previous_month,

            "group": top_group.get(group_col),

            "change": top_group.get("change"),

            "change_pct": top_group.get("change_pct")
        }

    else:

        question_stats["top_group"] = {

            "available": False,

            "reason": (
                "Not enough data: group-change analysis "
                "requires a date column, a grouping column, "
                "and at least two time periods."
            )
        }
    # =========================================================
    # QUESTION 3
    #
    # "Are there any anomalies?"
    #
    # Requires:
    #
    # value column
    #
    # This works even without a date column.
    # =========================================================

    if outliers is not None:

        question_stats["anomalies"] = {

            "available": True,

            "value_column": value_col,

            "outlier_count": len(outliers),

            "outliers": outliers[:20]
        }

    else:

        question_stats["anomalies"] = {

            "available": False,

            "reason": (
                "Not enough reliable numerical data "
                "to detect anomalies."
            )
        }

    # Add question statistics to the normal analysis response.

    result["question_stats"] = question_stats

    # =========================================================
    # UNAVAILABLE ANALYSES
    # =========================================================

    unavailable = []

    if not date_col:

        unavailable.append(
            "Trend analysis unavailable: no suitable date column was found."
        )

    if not group_col:

        unavailable.append(
            "Group analysis unavailable: no suitable categorical grouping column was found."
        )

    if unavailable:

        result["unavailable_analyses"] = unavailable

    # =========================================================
    # FINAL JSON SAFETY
    # =========================================================

    return sanitize_for_json(result)