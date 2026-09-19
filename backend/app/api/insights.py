import time
import hashlib

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.cleaning.pipeline import clean_dataframe
from app.analysis.insights_builder import build_insights
from app.api.upload import read_csv_safely
from app.question_cache import cache_question_stats

router = APIRouter()


@router.post("/insights")
async def get_insights(file: UploadFile = File(...)):
    total_start = time.perf_counter()

    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )

    # -------------------------
    # 1. Read uploaded file
    # -------------------------
    start = time.perf_counter()

    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()

    print(
        f"[PROFILE] file.read(): "
        f"{time.perf_counter() - start:.3f}s"
    )

    # -------------------------
    # 2. Parse CSV
    # -------------------------
    start = time.perf_counter()

    try:
        df, encoding_log = read_csv_safely(contents)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse CSV: {str(e)}"
        )

    print(
        f"[PROFILE] read_csv_safely(): "
        f"{time.perf_counter() - start:.3f}s"
    )

    print(f"[PROFILE] rows loaded: {len(df):,}")

    # -------------------------
    # 3. Cleaning
    # -------------------------
    start = time.perf_counter()

    cleaned_df, cleaning_report = clean_dataframe(df)

    print(
        f"[PROFILE] clean_dataframe(): "
        f"{time.perf_counter() - start:.3f}s"
    )

    # -------------------------
    # 4. Insights
    # -------------------------
    start = time.perf_counter()

    insights = build_insights(
        cleaned_df,
        cleaning_report["column_types"]
    )

    question_stats = insights.get("question_stats")
    if isinstance(question_stats, dict):
        cache_question_stats(file_hash, question_stats)

    print(
        f"[PROFILE] build_insights(): "
        f"{time.perf_counter() - start:.3f}s"
    )

    # -------------------------
    # Total
    # -------------------------
    total_time = time.perf_counter() - total_start

    print(
        f"[PROFILE] TOTAL: "
        f"{total_time:.3f}s"
    )

    return {
        "filename": file.filename,
        "cleaning_log": encoding_log + cleaning_report["changes"],
        "insights": insights
    }
