import pandas as pd
from difflib import SequenceMatcher


def normalize_category_column(
    series: pd.Series,
    similarity_threshold: float = 0.9
) -> tuple[pd.Series, list]:

    # Keep missing values as proper <NA>
    cleaned = series.astype("string").str.strip()

    # Work with unique values rather than all rows
    unique_values = cleaned.dropna().unique().tolist()

    # Normalize only the unique values
    title_map = {
        value: value.title()
        for value in unique_values
    }

    # High-cardinality columns:
    # normalize using a dictionary, but skip expensive fuzzy matching.
    if len(unique_values) > 300:
        cleaned = cleaned.map(title_map)

        return cleaned, [
            f"Skipped fuzzy matching ({len(unique_values)} unique values, exceeds performance threshold)"
        ]

    # Low-cardinality columns:
    # First normalize the unique values.
    normalized_values = [
        title_map[value]
        for value in unique_values
    ]

    merge_log = []
    canonical_map = {}

    for val in normalized_values:
        if val in canonical_map:
            continue

        canonical_map[val] = val

        for other in normalized_values:
            if other == val or other in canonical_map:
                continue

            similarity = SequenceMatcher(
                None,
                val.lower(),
                other.lower()
            ).ratio()

            if similarity >= similarity_threshold:
                canonical_map[other] = val

                merge_log.append(
                    f"Merged '{other}' into '{val}' "
                    f"(similarity: {similarity:.2f})"
                )

    # Build one mapping from original cleaned value → canonical value.
    final_map = {
        original: canonical_map.get(title_map[original], title_map[original])
        for original in unique_values
    }

    cleaned = cleaned.map(final_map)

    return cleaned, merge_log