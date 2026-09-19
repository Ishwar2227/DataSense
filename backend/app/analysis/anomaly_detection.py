import pandas as pd

def detect_outliers(df: pd.DataFrame, value_col: str, threshold: float = 3.0) -> list:
    """
    Flags rows where a numeric column is a statistical outlier,
    using the z-score method (how many standard deviations from the mean).
    Returns a list of flagged rows with their z-score.
    """
    values = df[value_col].dropna()
    mean = values.mean()
    std = values.std()

    if std == 0:
        return []  # no variation at all, nothing can be an outlier

    z_scores = (df[value_col] - mean) / std

    flagged = df[z_scores.abs() > threshold].copy()
    flagged["z_score"] = z_scores[z_scores.abs() > threshold]

    return flagged.to_dict(orient="records")