from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import hashlib
import json
import time

from app.cleaning.pipeline import clean_dataframe
from app.analysis.insights_builder import build_insights
from app.api.upload import read_csv_safely
from app.llm.groq_client import generate_answer
from app.question_cache import cache_question_stats, get_question_stats
from app.question_intent import detect_question_intent


router = APIRouter()


# =========================================================
# FIXED QUESTION TEMPLATES
# =========================================================

QUESTION_TEMPLATES = {
    "why_change": "Why did the value change?",
    "top_group": "Which group changed the most?",
    "anomalies": "Are there any anomalies?"
}


# =========================================================
# QUESTION ENDPOINT
# =========================================================

@router.post("/question")
async def answer_question(
    file: UploadFile = File(...),
    question_id: str | None = Form(None),
    question: str | None = Form(None)
):

    # -----------------------------------------------------
    # Validate file
    # -----------------------------------------------------

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )

    # -----------------------------------------------------
    # Resolve question
    # -----------------------------------------------------

    resolved_question_id = None
    display_question = None

    # -----------------------------------------------------
    # OPTION 1: Existing fixed question
    # -----------------------------------------------------

    if question_id:

        if question_id not in QUESTION_TEMPLATES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown question_id '{question_id}'. "
                    f"Available questions: "
                    f"{list(QUESTION_TEMPLATES.keys())}"
                )
            )

        resolved_question_id = question_id
        display_question = QUESTION_TEMPLATES[question_id]

    # -----------------------------------------------------
    # OPTION 2: New open-ended question
    # -----------------------------------------------------

    elif question:

        question = question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )

        resolved_question_id = detect_question_intent(question)

        if resolved_question_id is None:

            return {
                "question_id": None,
                "question": question,
                "stat": None,
                "answer": (
                    "I can't answer that question reliably "
                    "with the current DataSense analysis."
                )
            }

        display_question = question

    # -----------------------------------------------------
    # Neither question_id nor question provided
    # -----------------------------------------------------

    else:

        raise HTTPException(
            status_code=400,
            detail=(
                "Provide either 'question_id' for a fixed question "
                "or 'question' for an open-ended question."
            )
        )

    # -----------------------------------------------------
    # Read CSV
    # -----------------------------------------------------

    contents = await file.read()

    file_hash = hashlib.sha256(contents).hexdigest()

    request_start = time.perf_counter()

    question_stats = get_question_stats(file_hash)

    # -----------------------------------------------------
    # Cache MISS
    # -----------------------------------------------------

    if question_stats is None:

        try:
            df, _ = read_csv_safely(contents)

        except Exception as e:

            raise HTTPException(
                status_code=400,
                detail=f"Could not parse CSV: {str(e)}"
            )

        cleaned_df, cleaning_report = clean_dataframe(df)

        insights = build_insights(
            cleaned_df,
            cleaning_report["column_types"]
        )

        question_stats = insights.get(
            "question_stats",
            {}
        )

        cache_question_stats(
            file_hash,
            question_stats
        )

        print(
            f"[QUESTION_CACHE] miss; analysis completed in "
            f"{time.perf_counter() - request_start:.3f}s"
        )

    # -----------------------------------------------------
    # Cache HIT
    # -----------------------------------------------------

    else:

        print(
            f"[QUESTION_CACHE] hit; reused trusted statistics in "
            f"{time.perf_counter() - request_start:.3f}s"
        )

    # -----------------------------------------------------
    # Get trusted statistic
    # -----------------------------------------------------

    selected_stat = question_stats.get(
        resolved_question_id
    )

    # -----------------------------------------------------
    # Safety check
    # -----------------------------------------------------

    if selected_stat is None:

        raise HTTPException(
            status_code=500,
            detail=(
                "Question statistics were not generated "
                "for this question."
            )
        )

    # -----------------------------------------------------
    # NOT ENOUGH DATA FALLBACK
    # -----------------------------------------------------

    if not selected_stat.get("available", False):

        return {
            "question_id": resolved_question_id,
            "question": display_question,
            "stat": selected_stat,
            "answer": (
                "There is not enough data in this dataset "
                "to answer this question reliably."
            )
        }

    # -----------------------------------------------------
    # Prepare trusted statistics for the LLM
    # -----------------------------------------------------

    trusted_data = selected_stat.copy()

    # Do not send complete anomaly records to the LLM.
    # The LLM only needs the trusted anomaly count.

    if resolved_question_id == "anomalies":

        trusted_data.pop(
            "outliers",
            None
        )

    prompt = f"""
Question:
{display_question}

Trusted DataSense statistics:
{json.dumps(trusted_data, indent=2, default=str)}

Instructions:
- Answer the question using ONLY these statistics.
- Do not invent causes, events, or explanations.
- Do not calculate or assume information that is not provided.
- If the statistics do not explain the reason, explicitly say so.
- Mention the important numbers when relevant.
- Keep the answer concise and professional.
"""

    # -----------------------------------------------------
    # Generate LLM answer
    # -----------------------------------------------------

    try:

        answer = generate_answer(prompt)

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"LLM generation failed: {str(e)}"
        )

    # -----------------------------------------------------
    # Return trusted statistics + LLM explanation
    # -----------------------------------------------------

    return {
        "question_id": resolved_question_id,
        "question": display_question,
        "stat": selected_stat,
        "answer": answer
    }