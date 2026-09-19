import pandas as pd

def compute_monthly_trend(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """
    Aggregates a numeric column (e.g. Sales) by month.
    Returns a dataframe with columns: month, total, change_pct
    """
    temp = df[[date_col, value_col]].dropna().copy()
    temp["month"] = pd.to_datetime(temp[date_col]).dt.to_period("M")

    monthly = temp.groupby("month")[value_col].sum().reset_index()
    monthly = monthly.sort_values("month")

    # month-over-month % change — this is the number the FAQ layer will quote later
    monthly["change_pct"] = monthly[value_col].pct_change() * 100

    monthly["month"] = monthly["month"].astype(str)  # JSON can't serialize Period objects
    return monthly