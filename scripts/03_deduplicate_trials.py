import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "lai_clinical_trials_raw.xlsx"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = PROCESSED_DIR / "lai_clinical_trials_deduplicated.csv"
OUTPUT_XLSX = PROCESSED_DIR / "lai_clinical_trials_deduplicated.xlsx"


# -----------------------------
# Helper functions
# -----------------------------
def clean_text_value(value):
    """
    Convert missing values to empty string and strip unnecessary spaces.
    """
    if pd.isna(value):
        return ""

    return str(value).strip()


def unique_join(values, separator=" | "):
    """
    Join unique non-empty values while preserving readable output.
    """
    cleaned_values = []

    for value in values:
        value = clean_text_value(value)

        if value and value not in cleaned_values:
            cleaned_values.append(value)

    return separator.join(cleaned_values)


def first_non_empty(values):
    """
    Return the first non-empty value in a group.
    This is useful for trial-level fields that should be the same
    across duplicate rows for the same NCT ID.
    """
    for value in values:
        value = clean_text_value(value)

        if value:
            return value

    return ""


def main():
    print("Reading raw ClinicalTrials.gov dataset...")

    raw_df = pd.read_excel(RAW_FILE)

    print(f"Raw rows: {len(raw_df)}")
    print(f"Unique NCT IDs before deduplication: {raw_df['nct_id'].nunique()}")

    # -----------------------------
    # Columns to aggregate from multiple matched search rows
    # -----------------------------
    match_columns = [
        "matched_product_id",
        "matched_brand_name",
        "matched_api_name",
        "matched_category",
        "matched_search_term",
        "search_source",
    ]

    # -----------------------------
    # All other columns are study-level columns
    # For those, we keep the first non-empty value per NCT ID.
    # -----------------------------
    study_columns = [
        col for col in raw_df.columns
        if col not in match_columns and col != "nct_id"
    ]

    aggregation_rules = {}

    for col in match_columns:
        aggregation_rules[col] = unique_join

    for col in study_columns:
        aggregation_rules[col] = first_non_empty

    # -----------------------------
    # Deduplicate by NCT ID
    # -----------------------------
    dedup_df = (
        raw_df
        .groupby("nct_id", as_index=False)
        .agg(aggregation_rules)
    )

    # -----------------------------
    # Rename match columns to show they now contain multiple possible matches
    # -----------------------------
    dedup_df = dedup_df.rename(
        columns={
            "matched_product_id": "matched_product_ids",
            "matched_brand_name": "matched_brand_names",
            "matched_api_name": "matched_api_names",
            "matched_category": "matched_categories",
            "matched_search_term": "matched_search_terms",
            "search_source": "search_sources",
        }
    )

    # -----------------------------
    # Add useful count columns
    # -----------------------------
    dedup_df["number_of_matched_products"] = dedup_df["matched_product_ids"].apply(
        lambda x: len([item for item in str(x).split(" | ") if item.strip()])
    )

    dedup_df["number_of_matched_search_terms"] = dedup_df["matched_search_terms"].apply(
        lambda x: len([item for item in str(x).split(" | ") if item.strip()])
    )

    dedup_df["number_of_matched_categories"] = dedup_df["matched_categories"].apply(
        lambda x: len([item for item in str(x).split(" | ") if item.strip()])
    )

    # -----------------------------
    # Put important columns first
    # -----------------------------
    first_columns = [
        "nct_id",
        "brief_title",
        "official_title",
        "overall_status",
        "phases",
        "enrollment_count",
        "enrollment_type",
        "conditions",
        "intervention_names",
        "lead_sponsor_name",
        "unique_countries",
        "number_of_sites",
        "number_of_countries",
        "matched_product_ids",
        "matched_brand_names",
        "matched_api_names",
        "matched_categories",
        "matched_search_terms",
        "number_of_matched_products",
        "number_of_matched_search_terms",
        "number_of_matched_categories",
    ]

    remaining_columns = [col for col in dedup_df.columns if col not in first_columns]
    dedup_df = dedup_df[first_columns + remaining_columns]

    # -----------------------------
    # Save outputs
    # -----------------------------
    dedup_df.to_csv(OUTPUT_CSV, index=False)
    dedup_df.to_excel(OUTPUT_XLSX, index=False)

    print("\n======================================")
    print("Deduplication complete.")
    print(f"Deduplicated rows: {len(dedup_df)}")
    print(f"Unique NCT IDs after deduplication: {dedup_df['nct_id'].nunique()}")
    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved Excel: {OUTPUT_XLSX}")

    print("\nTop matched categories after deduplication:")
    print(dedup_df["matched_categories"].value_counts().head(20))

    print("\nDistribution of number of matched search terms:")
    print(dedup_df["number_of_matched_search_terms"].value_counts().sort_index())


if __name__ == "__main__":
    main()