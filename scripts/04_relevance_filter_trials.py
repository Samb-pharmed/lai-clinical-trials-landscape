import re
import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_deduplicated.xlsx"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = PROCESSED_DIR / "lai_clinical_trials_relevance_scored.csv"
OUTPUT_XLSX = PROCESSED_DIR / "lai_clinical_trials_relevance_scored.xlsx"


# -----------------------------
# Helper functions
# -----------------------------
def clean_text(value):
    """
    Convert missing values to clean lower-case text.
    """
    if pd.isna(value):
        return ""

    return str(value).lower().strip()


def contains_any(text, terms):
    """
    Return True if any term appears in the text.
    """
    text = clean_text(text)

    for term in terms:
        term = clean_text(term)

        if term and term in text:
            return True

    return False


def count_any(text, terms):
    """
    Count how many terms appear in the text.
    """
    text = clean_text(text)
    count = 0

    for term in terms:
        term = clean_text(term)

        if term and term in text:
            count += 1

    return count


def split_pipe_values(value):
    """
    Split values separated by ' | ' into a clean list.
    """
    value = clean_text(value)

    if not value:
        return []

    return [item.strip() for item in value.split("|") if item.strip()]


def build_search_term_list(row):
    """
    Build a set of possible relevant terms from matched search terms,
    brand names, API names, and common LAI language.
    """
    terms = []

    terms.extend(split_pipe_values(row.get("matched_search_terms", "")))
    terms.extend(split_pipe_values(row.get("matched_brand_names", "")))
    terms.extend(split_pipe_values(row.get("matched_api_names", "")))

    # Add generic LAI/depot keywords as supportive evidence
    lai_keywords = [
        "long acting",
        "long-acting",
        "extended release",
        "extended-release",
        "prolonged release",
        "prolonged-release",
        "sustained release",
        "sustained-release",
        "depot",
        "microsphere",
        "microspheres",
        "implant",
        "injectable suspension",
        "in-situ",
        "in situ",
        "liposome",
        "liposomal",
        "subcutaneous depot",
        "intramuscular depot",
    ]

    terms.extend(lai_keywords)

    # Remove duplicates while preserving order
    unique_terms = []
    for term in terms:
        term = clean_text(term)
        if term and term not in unique_terms:
            unique_terms.append(term)

    return unique_terms


def classify_relevance(score, intervention_match, title_match):
    """
    Convert relevance score into a human-readable flag.

    We intentionally keep 'Review' for ambiguous records.
    """
    if intervention_match and score >= 6:
        return "High"

    if intervention_match and score >= 4:
        return "Medium"

    if title_match and score >= 4:
        return "Medium"

    if score >= 3:
        return "Review"

    if score >= 1:
        return "Low"

    return "Low"


def find_false_positive_reason(row, intervention_match, title_match, summary_match, condition_match):
    """
    Create a simple explanation for why a trial may be noisy.
    """
    if intervention_match:
        return ""

    if title_match:
        return "Matched in title but not intervention fields"

    if summary_match:
        return "Matched mainly in summary/description, not intervention fields"

    if condition_match:
        return "Matched mainly in condition/keyword fields"

    return "Weak or indirect match"


def score_trial(row):
    """
    Score each trial based on where LAI/product terms are found.

    Logic:
    - Intervention fields are strongest evidence.
    - Arm descriptions are also strong.
    - Titles are medium-high evidence.
    - Summary/details are weaker.
    - Conditions alone are weak.
    """
    terms = build_search_term_list(row)

    intervention_text = " ".join([
        clean_text(row.get("intervention_names", "")),
        clean_text(row.get("intervention_descriptions", "")),
    ])

    arm_text = " ".join([
        clean_text(row.get("arm_group_labels", "")),
        clean_text(row.get("arm_group_descriptions", "")),
    ])

    title_text = " ".join([
        clean_text(row.get("brief_title", "")),
        clean_text(row.get("official_title", "")),
    ])

    summary_text = " ".join([
        clean_text(row.get("brief_summary", "")),
        clean_text(row.get("detailed_description", "")),
    ])

    condition_text = " ".join([
        clean_text(row.get("conditions", "")),
        clean_text(row.get("keywords", "")),
    ])

    # Match flags
    intervention_match = contains_any(intervention_text, terms)
    arm_match = contains_any(arm_text, terms)
    title_match = contains_any(title_text, terms)
    summary_match = contains_any(summary_text, terms)
    condition_match = contains_any(condition_text, terms)

    # Count how many product/LAI terms appear in stronger fields
    intervention_term_count = count_any(intervention_text, terms)
    title_term_count = count_any(title_text, terms)

    # Relevance score
    score = 0

    if intervention_match:
        score += 5

    if arm_match:
        score += 3

    if title_match:
        score += 3

    if summary_match:
        score += 1

    if condition_match:
        score += 1

    # Extra support if multiple terms appear in intervention/title
    if intervention_term_count >= 2:
        score += 1

    if title_term_count >= 2:
        score += 1

    relevance_flag = classify_relevance(
        score=score,
        intervention_match=intervention_match,
        title_match=title_match,
    )

    false_positive_reason = find_false_positive_reason(
        row=row,
        intervention_match=intervention_match,
        title_match=title_match,
        summary_match=summary_match,
        condition_match=condition_match,
    )

    return pd.Series({
        "relevance_score": score,
        "relevance_flag": relevance_flag,
        "match_in_intervention": intervention_match,
        "match_in_arm_description": arm_match,
        "match_in_title": title_match,
        "match_in_summary": summary_match,
        "match_in_condition": condition_match,
        "intervention_term_count": intervention_term_count,
        "title_term_count": title_term_count,
        "possible_false_positive_reason": false_positive_reason,
    })


def main():
    print("Reading deduplicated dataset...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Input rows: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    print("\nScoring trial relevance...")

    relevance_columns = df.apply(score_trial, axis=1)

    scored_df = pd.concat([df, relevance_columns], axis=1)

    # Put relevance columns near the front
    first_columns = [
        "nct_id",
        "relevance_flag",
        "relevance_score",
        "possible_false_positive_reason",
        "match_in_intervention",
        "match_in_arm_description",
        "match_in_title",
        "match_in_summary",
        "match_in_condition",
        "brief_title",
        "official_title",
        "overall_status",
        "phases",
        "enrollment_count",
        "conditions",
        "intervention_names",
        "matched_brand_names",
        "matched_api_names",
        "matched_categories",
        "matched_search_terms",
    ]

    remaining_columns = [col for col in scored_df.columns if col not in first_columns]
    scored_df = scored_df[first_columns + remaining_columns]

    # Save full scored dataset
    scored_df.to_csv(OUTPUT_CSV, index=False)
    scored_df.to_excel(OUTPUT_XLSX, index=False)

    print("\n======================================")
    print("Relevance scoring complete.")
    print(f"Rows scored: {len(scored_df)}")
    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved Excel: {OUTPUT_XLSX}")

    print("\nRelevance flag counts:")
    print(scored_df["relevance_flag"].value_counts())

    print("\nRelevance by matched category:")
    print(
        scored_df
        .groupby(["matched_categories", "relevance_flag"])
        .size()
        .sort_values(ascending=False)
        .head(30)
    )

    print("\nTop possible false-positive reasons:")
    print(scored_df["possible_false_positive_reason"].value_counts().head(10))


if __name__ == "__main__":
    main()