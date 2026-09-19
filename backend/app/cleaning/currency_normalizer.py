import pandas as pd


def normalize_currency_column(series: pd.Series) -> tuple[pd.Series, int]:
    """
    Strips currency symbols and commas, converts to plain float.
    Uses a fast path for already-numeric columns.
    Returns (cleaned_series, num_failed).
    """

    original_non_null = series.notna().sum()

    # Fast path: column is already numeric
    if pd.api.types.is_numeric_dtype(series):
        cleaned = pd.to_numeric(series, errors="coerce")

        num_failed = (
            cleaned.isna().sum()
            - series.isna().sum()
        )

        return cleaned, max(int(num_failed), 0)

    # Mixed/string currency values
    cleaned = series.astype("string").str.strip()

    cleaned = cleaned.str.replace(
        r"[^\d\.-]",
        "",
        regex=True
    )

    cleaned = pd.to_numeric(
        cleaned,
        errors="coerce"
    )

    num_failed = (
        cleaned.isna().sum()
        - series.isna().sum()
    )

    return cleaned, max(int(num_failed), 0)