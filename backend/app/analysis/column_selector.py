import re
import pandas as pd


# ============================================================
# GROUP COLUMN PREFERENCES
# ============================================================

PREFERRED_GROUP_KEYWORDS = [
    "region",
    "segment",
    "category",
    "department",
    "type",
    "class",
    "country",
    "state",
    "city",
    "borough",
    "group",
    "property",
    "status",
    "gender",
    "customer type",
    "program type",
    "old new",
    "grade level",
]


# ============================================================
# STRONG VALUE SIGNALS
# ============================================================

VALUE_KEYWORDS = [
    "sales",
    "revenue",
    "amount",
    "total",
    "value",
    "viewership",
    "rating",
    "score",
    "profit",
    "income",
    "spend",
    "price",
    "cost",
    "turnover",
    "duration",
    "temperature",
    "expense",
    "budget",
    "funding",
    "enrollment",
    "population",
]


# ============================================================
# WEAK / NEGATIVE VALUE SIGNALS
# ============================================================

WEAK_VALUE_KEYWORDS = [
    "id",
    "code",
    "number",
    "no",
    "row",
    "index",
    "season",
    "episode",
    "rank",
    "year",
    "month",
    "day",
    "quantity",
    "votes",
]


# ============================================================
# COLUMNS THAT SHOULD NOT BE USED AS MAIN VALUE
# ============================================================

EXCLUDED_VALUE_KEYWORDS = [
    "census tract",
    "census_tract",
    "postcode",
    "postal code",
    "postal_code",
    "zip",
    "zip code",
    "zip_code",
    "latitude",
    "longitude",
    "community board",
    "community_board",
    "community council",
    "community_council",
    "bin",
    "bbl",
    "geoid",
    "tract",
]


# ============================================================
# HELPER: NORMALIZE COLUMN NAME
# ============================================================

def _normalize_column_name(col: str) -> str:
    """
    Normalize a column name so matching works across:
        CustomerType
        Customer Type
        customer_type
        customer-type

    The function intentionally keeps words separated where
    possible so that 'customer' does not accidentally reject
    'CustomerType'.
    """

    text = str(col).strip()

    # Split camelCase / PascalCase.
    text = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])",
        " ",
        text
    )

    text = (
        text
        .replace("_", " ")
        .replace("-", " ")
    )

    # Remove punctuation.
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    # Collapse multiple spaces.
    text = re.sub(r"\s+", " ", text)

    return text.strip().lower()


# ============================================================
# HELPER: REPRESENTATIVE SAMPLE
# ============================================================

def _get_sample(series: pd.Series, max_rows: int = 20) -> pd.Series:
    """
    Returns a small representative sample instead of scanning
    the entire column.

    We take:
        - beginning of the dataset
        - end of the dataset
        - evenly spaced rows in between

    This is safer than using only df.head(20), because the
    beginning of a dataset may not represent the whole dataset.
    """

    if len(series) <= max_rows:
        return series

    # Number of rows from beginning/end.
    edge_count = min(5, max_rows // 4)

    head = series.head(edge_count)
    tail = series.tail(edge_count)

    remaining = max_rows - len(head) - len(tail)

    if remaining > 0:
        positions = (
            pd.Series(
                range(len(series))
            )
            .sample(
                n=min(remaining, len(series)),
                random_state=42
            )
            .sort_values()
        )

        middle = series.iloc[positions.tolist()]
    else:
        middle = series.iloc[0:0]

    sample = pd.concat(
        [head, middle, tail]
    )

    return sample[~sample.index.duplicated(keep="first")]


# ============================================================
# HELPER: EXCLUDED VALUE COLUMN
# ============================================================

def _is_excluded_value_column(col: str) -> bool:
    """
    Returns True when a numeric column is likely to be an
    identifier, geographic code, coordinate, etc.
    """

    name = _normalize_column_name(col)

    return any(
        keyword in name
        for keyword in EXCLUDED_VALUE_KEYWORDS
    )


# ============================================================
# HELPER: TOKEN MATCHING
# ============================================================

def _contains_keyword(name: str, keyword: str) -> bool:
    """
    Safe keyword matching.

    Example:

        'customer type' contains 'type' -> True
        'customer id' contains 'id' -> True

    But this avoids accidental substring problems such as
    treating 'customer' as a match inside 'customerType'.
    """

    name = _normalize_column_name(name)
    keyword = _normalize_column_name(keyword)

    if not name or not keyword:
        return False

    # Phrase match.
    if " " in keyword:
        return keyword in name

    # Whole-word match.
    return re.search(
        rf"\b{re.escape(keyword)}\b",
        name
    ) is not None


# ============================================================
# MAIN FUNCTION
# ============================================================

def select_analysis_columns(
    df: pd.DataFrame,
    column_types: dict
) -> dict:

    # =========================================================
    # SAFETY CHECK
    # =========================================================

    if df is None or df.empty:
        return {
            "date_col": None,
            "value_col": None,
            "group_col": None,
        }

    if not column_types:
        return {
            "date_col": None,
            "value_col": None,
            "group_col": None,
        }

    # =========================================================
    # DATE COLUMN
    # =========================================================

    date_cols = [
        col
        for col, t in column_types.items()
        if col in df.columns and t == "date"
    ]

    date_col = None

    if date_cols:

        def date_quality(col):

            sample = _get_sample(
                df[col]
            )

            missing = sample.isna().sum()

            return -missing

        date_col = max(
            date_cols,
            key=date_quality
        )

    # =========================================================
    # VALUE COLUMN
    # =========================================================

    numeric_types = {
        "currency",
        "decimal",
        "quantity",
    }

    numeric_cols = [
        col
        for col, t in column_types.items()
        if col in df.columns
        and t in numeric_types
    ]

    # ---------------------------------------------------------
    # Remove obvious identifiers / geographic codes.
    # ---------------------------------------------------------

    candidate_value_cols = [
        col
        for col in numeric_cols
        if not _is_excluded_value_column(col)
    ]

    value_col = None

    if candidate_value_cols:

        def value_score(col):

            name = _normalize_column_name(col)

            score = 0

            # -------------------------------------------------
            # Strong semantic metric keywords
            # -------------------------------------------------

            for i, keyword in enumerate(VALUE_KEYWORDS):

                if _contains_keyword(name, keyword):
                    score += 100 - i

            # -------------------------------------------------
            # Penalize weak metric candidates
            # -------------------------------------------------

            for keyword in WEAK_VALUE_KEYWORDS:

                if _contains_keyword(name, keyword):
                    score -= 60

            # -------------------------------------------------
            # Inspect representative sample
            # -------------------------------------------------

            sample = _get_sample(
                df[col]
            )

            numeric = pd.to_numeric(
                sample,
                errors="coerce"
            ).dropna()

            if len(numeric) == 0:
                return float("-inf")

            unique_count = numeric.nunique()

            # Constant values provide no useful trend/outlier
            # information.
            if unique_count <= 1:
                return float("-inf")

            # -------------------------------------------------
            # Prefer variation
            # -------------------------------------------------

            score += min(
                unique_count / 2,
                20
            )

            # -------------------------------------------------
            # Prefer good sample coverage
            # -------------------------------------------------

            coverage = (
                numeric.notna().sum()
                / max(len(sample), 1)
            )

            score += coverage * 10

            # -------------------------------------------------
            # Currency gets a small preference
            # -------------------------------------------------

            if column_types.get(col) == "currency":
                score += 15

            return score

        value_col = max(
            candidate_value_cols,
            key=value_score
        )

    # =========================================================
    # GROUP COLUMN
    # =========================================================

    group_col = None
    best_score = float("-inf")

    for col, col_type in column_types.items():

        # Column must actually exist.
        if col not in df.columns:
            continue

        # -----------------------------------------------------
        # Groups should primarily be categorical/text.
        # -----------------------------------------------------

        if col_type not in {
            "category",
            "text"
        }:
            continue

        # Never use date/value as group.
        if col == value_col or col == date_col:
            continue

        # -----------------------------------------------------
        # Representative sample.
        # -----------------------------------------------------

        sample = _get_sample(
            df[col]
        )

        sample = sample.dropna()

        if len(sample) == 0:
            continue

        # Convert to strings for safe categorical handling.
        sample = sample.astype(str).str.strip()

        # Remove empty strings.
        sample = sample[
            sample != ""
        ]

        if len(sample) == 0:
            continue

        n_unique = sample.nunique()

        # Need at least two groups.
        if n_unique < 2:
            continue

        name = _normalize_column_name(col)

        # =====================================================
        # IDENTIFIER / FREE-TEXT REJECTION
        # =====================================================
        #
        # IMPORTANT:
        #
        # We do NOT reject every column containing words like
        # "customer" or "product".
        #
        # Otherwise:
        #
        #     CustomerType
        #     ProductCategory
        #
        # could incorrectly be rejected.
        #
        # We reject actual identifier-style columns instead.
        # =====================================================

        identifier_patterns = [
            r"\bid\b",
            r"\bcode\b",
            r"\bnumber\b",
            r"\bno\b",
            r"\brow\b",
            r"\bindex\b",
            r"\bname\b",
            r"\baddress\b",
            r"\bphone\b",
            r"\bemail\b",
            r"\bdescription\b",
            r"\binvoice\b",
            r"\bstock\b",
        ]

        looks_like_identifier = any(
            re.search(
                pattern,
                name
            )
            for pattern in identifier_patterns
        )

        if looks_like_identifier:
            continue

        # -----------------------------------------------------
        # Detect preferred semantic grouping.
        # -----------------------------------------------------

        is_preferred_group = any(
            _contains_keyword(
                name,
                keyword
            )
            for keyword in PREFERRED_GROUP_KEYWORDS
        )

        # =====================================================
        # CARDINALITY RULES
        # =====================================================
        #
        # Normal categorical columns:
        #     <= 20 groups
        #
        # Strong semantic groups:
        #     <= 100 groups
        #
        # This prevents high-cardinality free text from being
        # selected as a chart grouping dimension.
        # =====================================================

        if is_preferred_group:

            if n_unique > 100:
                continue

        else:

            if n_unique > 20:
                continue

        # =====================================================
        # SCORE GROUP
        # =====================================================

        # Around 5 groups is convenient for a chart.
        if n_unique <= 20:

            score = -abs(
                n_unique - 5
            )

        else:

            score = -(
                n_unique / 20
            )

        # -----------------------------------------------------
        # Semantic preference.
        # -----------------------------------------------------

        if is_preferred_group:
            score += 20

        # -----------------------------------------------------
        # Explicit category inference bonus.
        # -----------------------------------------------------

        if col_type == "category":
            score += 5

        # -----------------------------------------------------
        # Coverage based on sample.
        # -----------------------------------------------------

        coverage = (
            sample.notna().sum()
            / max(len(_get_sample(df[col])), 1)
        )

        score += coverage * 5

        # -----------------------------------------------------
        # Slight preference for smaller, chart-friendly
        # categorical dimensions.
        # -----------------------------------------------------

        if 2 <= n_unique <= 10:
            score += 5

        # -----------------------------------------------------
        # Keep strongest candidate.
        # -----------------------------------------------------

        if score > best_score:
            best_score = score
            group_col = col

    # =========================================================
    # RETURN
    # =========================================================

    return {
        "date_col": date_col,
        "value_col": value_col,
        "group_col": group_col,
    }