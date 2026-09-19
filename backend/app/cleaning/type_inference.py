import pandas as pd
import re


# ---------------------------------------------------------------------------
# DataSense Column Type Inference
# ---------------------------------------------------------------------------
#
# Strategy:
#
#   1. Look at only a small sample of useful values.
#   2. Values are the PRIMARY evidence.
#   3. Column name is SECONDARY evidence.
#   4. Never scan the entire column just to calculate uniqueness.
#   5. Keep the returned type names compatible with the existing pipeline.
#
# Returned types:
#
#     date
#     currency
#     quantity
#     decimal
#     category
#     id
#     text
#
# ---------------------------------------------------------------------------


INFERENCE_SAMPLE_SIZE = 20


# ---------------------------------------------------------------------------
# DATE PATTERNS
# ---------------------------------------------------------------------------

DATE_PATTERNS = [

    # 2024-01-31
    # 2024-01-31 15:41
    r"^\d{4}-\d{1,2}-\d{1,2}(?:[T\s]+\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?$",

    # 2024/01/31
    # 2024/01/31 15:41
    r"^\d{4}/\d{1,2}/\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?$",

    # 2005-03
    # Useful for monthly datasets
    r"^\d{4}-\d{1,2}$",

    # 31-12-2023
    # 31/12/2023
    # 31-12-2023 15:41
    r"^\d{1,2}[-/]\d{1,2}[-/]\d{4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?$",
]


# ---------------------------------------------------------------------------
# CURRENCY
# ---------------------------------------------------------------------------
#
# Currency symbols are strong evidence.
#
# We DO NOT assume that every number with 2 decimal places is currency.
#
# Example:
#
#     $120.50      -> currency
#     ₹1,200.00    -> currency
#     17.20        -> could be Viewership / Rating / Rate
#
# ---------------------------------------------------------------------------

CURRENCY_PATTERN = (
    r"^[\$₹€£]\s*-?"
    r"(?:\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.\d+)?$"
)


# ---------------------------------------------------------------------------
# DECIMAL / NUMERIC
# ---------------------------------------------------------------------------

DECIMAL_PATTERN = r"^-?(?:\d+(?:\.\d+)?|\.\d+)$"


# ---------------------------------------------------------------------------
# COLUMN NAME HINTS
# ---------------------------------------------------------------------------
#
# These are ONLY hints.
#
# We do NOT blindly change the detected type just because the column name
# contains one of these words.
#
# The actual values still need to support the classification.
# ---------------------------------------------------------------------------

NAME_HINTS = {

    "id": [
        "id",
        "code",
        "number",
        "no",
        "invoice",
        "order",
        "customer id",
        "product id",
        "postal code",
        "postcode",
        "zip",
        "zip code",
        "census tract",
    ],

    "date": [
        "date",
        "time",
        "timestamp",
        "datetime",
        "year",
    ],

    "currency": [
        "price",
        "unit price",
        "sales",
        "sale",
        "profit",
        "cost",
        "amount",
        "revenue",
        "total",
        "income",
        "expense",
        "fee",
    ],

    "decimal": [
        "discount",
        "rate",
        "percent",
        "percentage",
        "ratio",
        "margin",
        "score",
        "viewership",
        "rating",
    ],

    "category": [
        "category",
        "type",
        "segment",
        "region",
        "country",
        "city",
        "state",
        "status",
        "gender",
        "class",
        "group",
    ],
}


# ---------------------------------------------------------------------------
# NORMALIZE COLUMN NAME
# ---------------------------------------------------------------------------

def _normalize_name(column_name: str) -> str:
    """
    Convert different naming styles into a common representation.

    Examples:

        CustomerType -> customer type
        unit_price   -> unit price
        Postal-Code  -> postal code
    """

    text = str(column_name).strip()

    # CamelCase -> Camel Case
    text = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        text
    )

    # Replace separators with spaces
    text = re.sub(
        r"[_\-./]+",
        " ",
        text
    )

    # Remove remaining punctuation
    text = re.sub(
        r"[^A-Za-z0-9 ]+",
        " ",
        text
    )

    # Collapse spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip().lower()


# ---------------------------------------------------------------------------
# FIND NAME HINT
# ---------------------------------------------------------------------------

def _name_hint(column_name: str):
    """
    Return a semantic hint from the column name.

    Returns:
        "id"
        "date"
        "currency"
        "decimal"
        "category"
        None
    """

    normalized = _normalize_name(column_name)

    words = set(
        normalized.split()
    )

    # ---------------------------------------------------------------
    # First check multi-word hints
    # ---------------------------------------------------------------

    for hint_type, keywords in NAME_HINTS.items():

        for keyword in keywords:

            keyword_normalized = _normalize_name(keyword)

            if (
                " " in keyword_normalized
                and keyword_normalized in normalized
            ):
                return hint_type

    # ---------------------------------------------------------------
    # Then check individual words
    # ---------------------------------------------------------------

    for hint_type, keywords in NAME_HINTS.items():

        for keyword in keywords:

            keyword_normalized = _normalize_name(keyword)

            if (
                " " not in keyword_normalized
                and keyword_normalized in words
            ):
                return hint_type

    return None


# ---------------------------------------------------------------------------
# BACKWARD-COMPATIBLE NAME HINT FUNCTION
# ---------------------------------------------------------------------------

def apply_name_hint(
    column_name: str,
    detected_type: str
) -> str:
    """
    Keep compatibility with the previous pipeline.

    IMPORTANT:

    The column name does NOT blindly override the value-based detection.

    It only helps when the detected type is generic or ambiguous.
    """

    hint = _name_hint(column_name)

    if hint is None:
        return detected_type

    # Generic text/category can be refined by a strong semantic hint.
    if detected_type in {"text", "category"}:

        if hint in {
            "category",
            "id",
            "date",
        }:
            return hint

    # Numeric types can be refined by meaningful names.
    if detected_type in {
        "quantity",
        "decimal",
    }:

        if hint in {
            "currency",
            "decimal",
            "id",
        }:
            return hint

    # Otherwise trust the actual values.
    return detected_type


# ---------------------------------------------------------------------------
# TAKE SAMPLE
# ---------------------------------------------------------------------------

def _sample_values(
    series: pd.Series,
    sample_size: int
) -> pd.Series:
    """
    Take only the first N useful values.

    This is intentionally NOT:

        series.astype(str)

    on the entire column.

    Only the small sample is converted when necessary.
    """

    # Remove missing values first.
    sample = series.dropna().head(sample_size)

    if sample.empty:
        return sample

    # Remove blank strings.
    if (
        pd.api.types.is_string_dtype(sample)
        or sample.dtype == object
    ):

        mask = (
            sample
            .astype(str)
            .str.strip()
            .ne("")
        )

        sample = sample.loc[mask]

    return sample


# ---------------------------------------------------------------------------
# DATE MATCHING
# ---------------------------------------------------------------------------

def _date_match_ratio(
    sample: pd.Series
) -> float:

    if sample.empty:
        return 0.0

    def looks_like_date(value) -> bool:

        # Already parsed datetime
        if isinstance(value, pd.Timestamp):

            return not pd.isna(value)

        text = str(value).strip()

        # First check the shape.
        pattern_match = any(
            re.fullmatch(
                pattern,
                text
            )
            for pattern in DATE_PATTERNS
        )

        if not pattern_match:
            return False

        # Then make sure pandas can actually parse it.
        try:

            parsed = pd.to_datetime(
                text,
                errors="coerce"
            )

            return not pd.isna(parsed)

        except Exception:

            return False

    matches = sample.map(
        looks_like_date
    )

    return float(
        matches.mean()
    )


# ---------------------------------------------------------------------------
# NUMERIC CONVERSION
# ---------------------------------------------------------------------------

def _numeric_values(
    sample: pd.Series
) -> pd.Series:

    if sample.empty:
        return pd.Series(
            dtype="float64"
        )

    return pd.to_numeric(
        sample
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False
        )
        .str.strip(),
        errors="coerce",
    )


# ---------------------------------------------------------------------------
# CURRENCY MATCHING
# ---------------------------------------------------------------------------

def _currency_match_ratio(
    sample: pd.Series
):

    if sample.empty:
        return 0.0, False

    matches = (
        sample
        .astype(str)
        .str.strip()
        .map(
            lambda value: bool(
                re.fullmatch(
                    CURRENCY_PATTERN,
                    value
                )
            )
        )
    )

    return (
        float(matches.mean()),
        bool(matches.any())
    )


# ---------------------------------------------------------------------------
# DECIMAL MATCHING
# ---------------------------------------------------------------------------

def _decimal_match_ratio(
    sample: pd.Series
) -> float:

    if sample.empty:
        return 0.0

    matches = (
        sample
        .astype(str)
        .str.strip()
        .map(
            lambda value: bool(
                re.fullmatch(
                    DECIMAL_PATTERN,
                    value
                )
            )
        )
    )

    return float(
        matches.mean()
    )


# ---------------------------------------------------------------------------
# INTEGER MATCHING
# ---------------------------------------------------------------------------

def _integer_match_ratio(
    sample: pd.Series
) -> float:

    if sample.empty:
        return 0.0

    numeric = _numeric_values(
        sample
    )

    if numeric.empty:
        return 0.0

    original = (
        sample
        .astype(str)
        .str.strip()
        .str.replace(
            ",",
            "",
            regex=False
        )
    )

    integer_like = []

    for original_value, numeric_value in zip(
        original,
        numeric
    ):

        if pd.isna(numeric_value):

            integer_like.append(False)

            continue

        # Accept:
        #
        #   5
        #   -5
        #   5.0
        #   5.00
        #
        integer_like.append(
            bool(
                re.fullmatch(
                    r"-?\d+(?:\.0+)?",
                    original_value
                )
            )
        )

    return float(
        sum(integer_like) / len(integer_like)
    )


# ---------------------------------------------------------------------------
# IDENTIFIER SHAPE
# ---------------------------------------------------------------------------

def _looks_identifier_like(
    sample: pd.Series
) -> float:
    """
    Determine whether values LOOK like identifiers.

    Examples that can look like IDs:

        C537630
        US-2017-168116
        TB-21520
        411001

    Examples that should NOT automatically become IDs:

        Amazon Fee
        John Smith
        Monochrome Laser Printer
    """

    if sample.empty:
        return 0.0

    def identifier_shape(value) -> bool:

        text = str(value).strip()

        if not text:
            return False

        # Normal descriptive text usually contains spaces.
        if " " in text:
            return False

        # Identifier/code style.
        if re.fullmatch(
            r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*",
            text
        ):
            return True

        return False

    matches = sample.map(
        identifier_shape
    )

    return float(
        matches.mean()
    )


# ---------------------------------------------------------------------------
# CATEGORY DETECTION
# ---------------------------------------------------------------------------

def _looks_category_like(
    sample: pd.Series,
    unique_count: int
) -> bool:
    """
    Detect small categorical domains from the sample.

    Examples:

        Member
        Premium
        Regular

    or:

        East
        West
        South
        Central
    """

    if sample.empty:
        return False

    sample_size = len(sample)

    if unique_count <= 1:
        return False

    # Very small categorical domain.
    if (
        unique_count <= 8
        and sample_size >= 5
    ):
        return True

    # Slightly larger categorical domain.
    if (
        unique_count <= 20
        and unique_count <= sample_size * 0.5
    ):
        return True

    return False


# ---------------------------------------------------------------------------
# MAIN TYPE DETECTION
# ---------------------------------------------------------------------------

def detect_column_type(
    series: pd.Series,
    column_name=None,
    sample_size: int = INFERENCE_SAMPLE_SIZE
) -> str:
    """
    Infer a column type using only a small sample.

    Detection order:

        1. Date
        2. Currency
        3. Identifier
        4. Category
        5. Quantity
        6. Decimal
        7. Text
    """

    # ---------------------------------------------------------------
    # Get sample
    # ---------------------------------------------------------------

    sample = _sample_values(
        series,
        sample_size
    )

    if sample.empty:
        return "text"

    # ---------------------------------------------------------------
    # Get column-name hint
    # ---------------------------------------------------------------

    name_hint = None

    if column_name is not None:

        name_hint = _name_hint(
            column_name
        )

    # ---------------------------------------------------------------
    # 1. DATE
    # ---------------------------------------------------------------

    # If pandas already recognizes the column as datetime,
    # this is very strong evidence.
    if pd.api.types.is_datetime64_any_dtype(
        series
    ):
        return "date"

    date_ratio = _date_match_ratio(
        sample
    )

    if date_ratio >= 0.80:
        return "date"

    # If the name says Date/Time, allow pandas to resolve
    # slightly unusual date formats.
    if name_hint == "date":

        try:

            parsed = pd.to_datetime(
                sample,
                errors="coerce"
            )

            if (
                parsed.notna().mean()
                >= 0.80
            ):
                return "date"

        except Exception:
            pass

    # ---------------------------------------------------------------
    # 2. CURRENCY
    # ---------------------------------------------------------------

    (
        currency_ratio,
        has_currency_symbol
    ) = _currency_match_ratio(
        sample
    )

    # Explicit symbols are strong evidence.
    if currency_ratio >= 0.80:
        return "currency"

    # Plain numeric money values such as:
    #
    #     Sales = 3083.43
    #     UnitPrice = 120.50
    #
    # can be identified using the column name as a secondary hint.

    numeric = _numeric_values(
        sample
    )

    if (
        name_hint == "currency"
        and numeric.notna().mean() >= 0.80
    ):
        return "currency"

        # ---------------------------------------------------------------
        # 3. IDENTIFIER
        # ---------------------------------------------------------------

        identifier_ratio = _looks_identifier_like(
            sample
        )

        # ---------------------------------------------------------------
        # IMPORTANT:
        #
        # A semantic category name such as:
        #
        #     Type
        #     Region
        #     Country
        #     Category
        #     Segment
        #
        # must NOT be classified as an ID merely because its values
        # happen to look like simple words/codes.
        #
        # Example:
        #
        #     Type
        #     Hyper
        #     Express
        #
        # "Hyper" and "Express" look identifier-like to the generic
        # shape detector, but the column itself clearly represents
        # categories.
        # ---------------------------------------------------------------

        if (
            name_hint == "category"
            and not pd.api.types.is_numeric_dtype(series)
        ):
            return "category"


        # ---------------------------------------------------------------
        # Strong name + identifier-like values.
        #
        # Example:
        #
        #     Customer ID
        #     Product ID
        #     Invoice Number
        #     Order ID
        #
        # These should remain IDs.
        # ---------------------------------------------------------------

        if (
            name_hint == "id"
            and identifier_ratio >= 0.60
        ):
            return "id"


        # ---------------------------------------------------------------
        # Generic identifier detection.
        #
        # Only use this when the column does NOT have a strong
        # categorical semantic hint.
        # ---------------------------------------------------------------

        if (
            identifier_ratio >= 0.90
            and not pd.api.types.is_numeric_dtype(series)
        ):
            return "id"

    # ---------------------------------------------------------------
    # 4. CATEGORY
    # ---------------------------------------------------------------

    sample_unique = int(
        sample.nunique(
            dropna=True
        )
    )

    if _looks_category_like(
        sample,
        sample_unique
    ):
        return "category"

    # A column called Region/Country/Type/etc. is a useful hint.
    #
    # But only use this for non-numeric data.
    if (
        name_hint == "category"
        and not numeric.notna().all()
    ):
        return "category"

    # ---------------------------------------------------------------
    # 5. QUANTITY / INTEGER
    # ---------------------------------------------------------------

    integer_ratio = _integer_match_ratio(
        sample
    )

    if integer_ratio >= 0.80:

        # If the name strongly indicates an ID,
        # respect that rather than calling it quantity.
        if name_hint == "id":
            return "id"

        return "quantity"

    # ---------------------------------------------------------------
    # 6. DECIMAL / NUMERIC MEASUREMENT
    # ---------------------------------------------------------------

    decimal_ratio = _decimal_match_ratio(
        sample
    )

    if decimal_ratio >= 0.80:

        if name_hint == "currency":
            return "currency"

        return "decimal"

    # Mixed numeric formatting:
    #
    #     17
    #     17.2
    #     18.05
    #     19
    #
    # is still numeric.

    if (
        numeric.notna().mean()
        >= 0.80
    ):

        if name_hint == "currency":
            return "currency"

        if name_hint == "decimal":
            return "decimal"

        if name_hint == "id":
            return "id"

        return "decimal"

    # ---------------------------------------------------------------
    # 7. TEXT
    # ---------------------------------------------------------------

    return "text"


# ---------------------------------------------------------------------------
# INFER ALL COLUMNS
# ---------------------------------------------------------------------------

def infer_all_columns(
    df: pd.DataFrame,
    sample_size: int = INFERENCE_SAMPLE_SIZE
) -> dict:
    """
    Infer every column independently.

    Only the first `sample_size` useful values of each column
    are inspected.

    If an unexpected problem occurs for one column, that column
    safely falls back to "text" so the backend does not crash.
    """

    result = {}

    for col in df.columns:

        try:

            result[col] = detect_column_type(
                df[col],
                column_name=str(col),
                sample_size=sample_size
            )

        except Exception:

            # VERY IMPORTANT:
            #
            # One strange column should never crash the whole
            # DataSense backend.
            #
            # If something unexpected happens, safely classify
            # that column as text and continue processing.
            result[col] = "text"

    return result