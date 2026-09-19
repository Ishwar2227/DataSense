import pandas as pd
def find_top_contributors(df: pd.DataFrame, date_col: str, value_col: str,
                            group_col: str, target_month: str, compare_month: str) -> list:
    temp = df[[date_col, value_col, group_col]].dropna().copy()
    temp["month"] = pd.to_datetime(temp[date_col]).dt.to_period("M").astype(str)

    target = temp[temp["month"] == target_month].groupby(group_col)[value_col].sum()
    compare = temp[temp["month"] == compare_month].groupby(group_col)[value_col].sum()

    combined = pd.DataFrame({"target": target, "compare": compare}).fillna(0)
    combined["change"] = combined["target"] - combined["compare"]
    combined["change_pct"] = ((combined["target"] - combined["compare"]) / combined["compare"].replace(0, pd.NA)) * 100

    # Sort by the SIZE of the change (biggest mover first), regardless of
    # direction — this way "top contributor" is correct whether the overall
    # trend is a spike or a drop. Caller can check the sign of `change` to
    # know whether it helped or hurt.
    combined = combined.reindex(combined["change"].abs().sort_values(ascending=False).index)

    return combined.reset_index().to_dict(orient="records")