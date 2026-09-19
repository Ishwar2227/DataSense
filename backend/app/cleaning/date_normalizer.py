import pandas as pd


def normalize_date_column(series: pd.Series) -> tuple[pd.Series, int]:
    """
    Converts a messy date column into a consistent datetime format.

    Strategy:
    1. Try common explicit formats first.
    2. Only send values that failed those formats to the slower
       mixed-format parser.
    3. Return (cleaned_series, num_failed).
    """

    original_non_null = series.notna().sum()

    if original_non_null == 0:
        return pd.to_datetime(series, errors="coerce"), 0

    # Start with an empty datetime result.
    cleaned = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")

    # Common date formats, ordered from most specific/common to more flexible.
    formats = [
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
    ]

    remaining = series.notna()

    for fmt in formats:
        if not remaining.any():
            break

        parsed = pd.to_datetime(
            series[remaining],
            errors="coerce",
            format=fmt
        )

        success = parsed.notna()

        if success.any():
            cleaned.loc[parsed.index[success]] = parsed[success]

        # Only try another format on values still unresolved.
        remaining.loc[parsed.index] = ~success

    # Slow fallback ONLY for values that still failed.
    if remaining.any():
        fallback = pd.to_datetime(
            series[remaining],
            errors="coerce",
            format="mixed"
        )

        cleaned.loc[fallback.index] = fallback

    num_failed = int(
        original_non_null - cleaned.notna().sum()
    )

    num_failed = max(num_failed, 0)

    return cleaned, num_failed