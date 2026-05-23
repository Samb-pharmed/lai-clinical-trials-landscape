import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_strict_enhanced.xlsx"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = PROCESSED_DIR / "lai_clinical_trials_development_subset.csv"
OUTPUT_XLSX = PROCESSED_DIR / "lai_clinical_trials_development_subset.xlsx"


# -----------------------------
# Helper functions
# -----------------------------
def add_development_flags(df):
    development_phases = [
        "EARLY_PHASE1",
        "PHASE1",
        "PHASE1 | PHASE2",
        "PHASE2",
        "PHASE2 | PHASE3",
        "PHASE3",
    ]

    df = df.copy()

    df["phase_1_to_3_flag"] = df["phase_clean"].isin(development_phases)

    df["interventional_flag"] = (
        df["study_type"]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq("INTERVENTIONAL")
    )

    df["development_subset_flag"] = (
        df["phase_1_to_3_flag"] & df["interventional_flag"]
    )

    df["enrollment_over_10000_flag"] = df["enrollment_count_clean"] > 10000
    df["enrollment_over_5000_flag"] = df["enrollment_count_clean"] > 5000

    return df


def main():
    print("Reading strict enhanced dataset...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Input rows: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    df = add_development_flags(df)

    development_df = df[df["development_subset_flag"]].copy()

    # Put key columns first
    first_columns = [
        "nct_id",
        "development_subset_flag",
        "interventional_flag",
        "phase_1_to_3_flag",
        "enrollment_over_10000_flag",
        "enrollment_over_5000_flag",
        "therapeutic_area_clean",
        "product_family_clean",
        "sponsor_normalized",
        "phase_clean",
        "overall_status",
        "study_type",
        "enrollment_count_clean",
        "enrollment_type",
        "start_year",
        "primary_completion_year",
        "completion_year",
        "duration_to_primary_completion_months",
        "duration_to_study_completion_months",
        "brief_title",
        "conditions",
        "intervention_names",
        "lead_sponsor_name",
        "lead_sponsor_class",
        "unique_countries",
        "number_of_sites",
        "number_of_countries",
        "matched_brand_names",
        "matched_api_names",
        "matched_categories",
        "matched_search_terms",
    ]

    remaining_columns = [col for col in development_df.columns if col not in first_columns]
    development_df = development_df[first_columns + remaining_columns]

    development_df.to_csv(OUTPUT_CSV, index=False)
    development_df.to_excel(OUTPUT_XLSX, index=False)

    print("\n======================================")
    print("Development subset created.")
    print(f"Rows saved: {len(development_df)}")
    print(f"Unique NCT IDs: {development_df['nct_id'].nunique()}")
    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved Excel: {OUTPUT_XLSX}")

    print("\nPhase counts:")
    print(development_df["phase_clean"].value_counts())

    print("\nTherapeutic area counts:")
    print(development_df["therapeutic_area_clean"].value_counts())

    print("\nTop product families:")
    print(development_df["product_family_clean"].value_counts().head(20))

    print("\nEnrolment outlier flags:")
    print("Trials > 5,000:", development_df["enrollment_over_5000_flag"].sum())
    print("Trials > 10,000:", development_df["enrollment_over_10000_flag"].sum())

    print("\nMedian enrolment:", development_df["enrollment_count_clean"].median())
    print("Mean enrolment:", round(development_df["enrollment_count_clean"].mean(), 1))


if __name__ == "__main__":
    main()