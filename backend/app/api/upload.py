from fastapi import APIRouter, UploadFile, File, HTTPException
from app.cleaning.type_inference import infer_all_columns
from app.cleaning.pipeline import clean_dataframe

import pandas as pd
import io
import chardet

router = APIRouter()


def read_csv_safely(contents: bytes):
    """
    Reads CSV files efficiently while handling non-UTF-8 encodings.

    Strategy:
    1. Try UTF-8 first.
    2. If UTF-8 fails, detect encoding from a small sample.
    3. Read the full CSV using the detected encoding.
    4. Fall back to latin-1 if detection/reading fails.

    Returns:
        (dataframe, cleaning_log)
    """
    cleaning_log = []

    # Step 1: Try UTF-8 first.
    # This is the normal fast path.
    try:
        df = pd.read_csv(
            io.BytesIO(contents),
            encoding="utf-8"
        )
        return df, cleaning_log

    except UnicodeDecodeError:
        pass

    # Step 2: Detect encoding from only a sample.
    # Do NOT run chardet over the entire file.
    sample_size = min(len(contents), 1_000_000)
    sample = contents[:sample_size]

    detected = chardet.detect(sample)
    encoding = detected.get("encoding") or "latin-1"

    # Step 3: Try the detected encoding on the full file.
    try:
        df = pd.read_csv(
            io.BytesIO(contents),
            encoding=encoding
        )

        cleaning_log.append(
            f"Detected non-UTF-8 encoding ({encoding}), converted automatically"
        )

        return df, cleaning_log

    except Exception:
        # Step 4: Last-resort fallback.
        df = pd.read_csv(
            io.BytesIO(contents),
            encoding="latin-1"
        )

        cleaning_log.append(
            "Encoding detection failed, forced latin-1 as fallback "
            "(some characters may be imperfect)"
        )

        return df, cleaning_log

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    contents = await file.read()
    try:
        df, encoding_log = read_csv_safely(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

    cleaned_df, report = clean_dataframe(df)
    all_changes = encoding_log + report["changes"]

    return {
        "filename": file.filename,
        "rows": len(cleaned_df),
        "columns": list(cleaned_df.columns),
        "column_types": report["column_types"],
        "cleaning_log": all_changes,
        "preview": cleaned_df.head(5).to_dict(orient="records")
    }