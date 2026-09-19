import pandas as pd
from app.cleaning.type_inference import infer_all_columns
from app.cleaning.date_normalizer import normalize_date_column
from app.cleaning.currency_normalizer import normalize_currency_column
from app.cleaning.category_matcher import normalize_category_column


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Runs the full cleaning pipeline on a raw dataframe.
    Returns (cleaned_df, report) where report contains column types
    and a log of every change made.
    """
    column_types = infer_all_columns(df)
    cleaned_df = df.copy()
    report = {
        "column_types": column_types,
        "changes": []
    }

    for col, col_type in column_types.items():
        if col_type == "date":
            cleaned_df[col], num_failed = normalize_date_column(df[col])
            if num_failed > 0:
                report["changes"].append(
                    f"'{col}': {num_failed} value(s) could not be parsed as dates, set to missing"
                )

        elif col_type == "currency":
            cleaned_df[col], num_failed = normalize_currency_column(df[col])
            if num_failed > 0:
                report["changes"].append(
                    f"'{col}': {num_failed} value(s) could not be converted to numbers, set to missing"
                )

        elif col_type == "category":
            cleaned_df[col], merge_log = normalize_category_column(df[col])
            report["changes"].extend([f"{col}: {msg}" for msg in merge_log])

        # id, quantity, decimal, text — left as-is for now, no cleaner built yet for these

    return cleaned_df, report