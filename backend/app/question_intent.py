import re


# =========================================================
# SUPPORTED QUESTION INTENTS
# =========================================================

SUPPORTED_INTENTS = {
    "why_change": "Why did the value change?",
    "top_group": "Which group changed the most?",
    "anomalies": "Are there any anomalies?",
}


# =========================================================
# QUESTION NORMALIZATION
# =========================================================

def normalize_question(question: str) -> str:
    """
    Normalize a user's typed question so intent matching
    is consistent.
    """

    question = question.lower().strip()

    question = re.sub(
        r"[^a-z0-9\s]",
        " ",
        question
    )

    question = re.sub(
        r"\s+",
        " ",
        question
    )

    return question


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_question_intent(question: str):
    """
    Map a natural-language question to one of the
    supported DataSense question intents.

    Returns:
        "why_change"
        "top_group"
        "anomalies"
        None
    """

    question = normalize_question(question)

    # -----------------------------------------------------
    # ANOMALIES
    # -----------------------------------------------------

    anomaly_patterns = [
        r"\banomal",
        r"\boutlier",
        r"\bunusual\b",
        r"\babnormal\b",
        r"\bodd\b",
        r"\bspike\b",
        r"\bdip\b",
    ]

    if any(
        re.search(pattern, question)
        for pattern in anomaly_patterns
    ):
        return "anomalies"

    # -----------------------------------------------------
    # TOP GROUP / GROUP CHANGE
    # -----------------------------------------------------

    group_patterns = [
        r"\bwhich .*region.*(change|grow|increase|decrease|decline)",
        r"\bwhich .*group.*(change|grow|increase|decrease|decline)",
        r"\bwhich .*category.*(change|grow|increase|decrease|decline)",
        r"\bwhich .*country.*(change|grow|increase|decrease|decline)",
        r"\bwhich .*store.*(change|grow|increase|decrease|decline)",
        r"\bwhich .*segment.*(change|grow|increase|decrease|decline)",
        r"\bwhich .*changed the most\b",
        r"\bwhich .*grew the most\b",
        r"\bwhich .*increased the most\b",
        r"\bwhich .*decreased the most\b",
        r"\bwhich .*declined the most\b",
    ]

    if any(
        re.search(pattern, question)
        for pattern in group_patterns
    ):
        return "top_group"

    # -----------------------------------------------------
    # VALUE CHANGE
    # -----------------------------------------------------

    change_patterns = [
        r"\bwhy .*change",
        r"\bwhy .*changed",
        r"\bwhy .*increase",
        r"\bwhy .*increased",
        r"\bwhy .*decrease",
        r"\bwhy .*decreased",
        r"\bwhy .*decline",
        r"\bwhy .*declined",
        r"\bwhy .*fall",
        r"\bwhy .*fell",
        r"\bwhy .*drop",
        r"\bwhy .*dropped",
        r"\bwhy .*rise",
        r"\bwhy .*rose",
        r"\bwhy .*grew",
        r"\bwhy .*growth",
        r"\bdid .*change",
        r"\bdid .*increase",
        r"\bdid .*decrease",
        r"\bdid .*fall",
        r"\bdid .*rise",
        r"\bwhat caused .*change",
        r"\bwhat caused .*drop",
        r"\bwhat caused .*increase",
    ]

    if any(
        re.search(pattern, question)
        for pattern in change_patterns
    ):
        return "why_change"

    # -----------------------------------------------------
    # UNSUPPORTED
    # -----------------------------------------------------

    return None