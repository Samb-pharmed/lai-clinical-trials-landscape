import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_strict_enhanced.xlsx"

TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TABLES_DIR / "strict_14_qc_outliers_and_active_trials.xlsx"


# -----------------------------
# Helper functions
# -----------------------------
def save_multi_sheet_excel(output_path, sheet_dict):
    """
    Save multiple dataframes into one Excel file, each as a separate sheet.
    """
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in sheet_dict.items():
            safe_sheet_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)


def select_core_columns(df):
    """
    Keep the most useful columns for QC review.
    """
    columns = [
        "nct_id",
        "brief_title",
        "official_title",
        "overall_status",
        "study_type",
        "phase_clean",
        "therapeutic_area_clean",
        "product_family_clean",
        "enrollment_count_clean",
        "enrollment_type",
        "start_year",
        "completion_year",
        "lead_sponsor_name",
        "sponsor_normalized",
        "conditions",
        "intervention_names",
        "unique_countries",
        "number_of_sites",
        "number_of_countries",
        "matched_brand_names",
        "matched_api_names",
        "matched_search_terms",
    ]

    available_columns = [col for col in columns if col in df.columns]
    return df[available_columns].copy()


def add_active_status_flag(df):
    """
    Create an active trial flag.
    """
    active_statuses = [
        "RECRUITING",
        "NOT_YET_RECRUITING",
        "ACTIVE_NOT_RECRUITING",
        "ENROLLING_BY_INVITATION",
    ]

    df = df.copy()
    df["active_trial_flag"] = df["overall_status"].isin(active_statuses)
    return df


def add_development_phase_flag(df):
    """
    Flag development-relevant Phase 1–3 interventional trials.
    """
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

    df["development_relevant_flag"] = (
        df["phase_1_to_3_flag"] & df["interventional_flag"]
    )

    return df


def create_product_family_summary(df):
    """
    Product family-level summary with trial count, active count, and enrolment statistics.
    """
    summary = (
        df
        .groupby("product_family_clean")
        .agg(
            trial_count=("nct_id", "count"),
            active_trials=("active_trial_flag", "sum"),
            development_relevant_trials=("development_relevant_flag", "sum"),
            median_enrollment=("enrollment_count_clean", "median"),
            mean_enrollment=("enrollment_count_clean", "mean"),
            max_enrollment=("enrollment_count_clean", "max"),
            median_sites=("number_of_sites", "median"),
            median_countries=("number_of_countries", "median"),
        )
        .reset_index()
        .sort_values("trial_count", ascending=False)
    )

    summary["mean_enrollment"] = summary["mean_enrollment"].round(1)
    summary["median_enrollment"] = summary["median_enrollment"].round(1)
    summary["median_sites"] = summary["median_sites"].round(1)
    summary["median_countries"] = summary["median_countries"].round(1)

    return summary


def create_therapeutic_area_summary(df):
    """
    Therapeutic area-level summary with trial count, active count, and enrolment statistics.
    """
    summary = (
        df
        .groupby("therapeutic_area_clean")
        .agg(
            trial_count=("nct_id", "count"),
            active_trials=("active_trial_flag", "sum"),
            development_relevant_trials=("development_relevant_flag", "sum"),
            median_enrollment=("enrollment_count_clean", "median"),
            mean_enrollment=("enrollment_count_clean", "mean"),
            max_enrollment=("enrollment_count_clean", "max"),
            median_sites=("number_of_sites", "median"),
            median_countries=("number_of_countries", "median"),
        )
        .reset_index()
        .sort_values("trial_count", ascending=False)
    )

    summary["mean_enrollment"] = summary["mean_enrollment"].round(1)
    summary["median_enrollment"] = summary["median_enrollment"].round(1)
    summary["median_sites"] = summary["median_sites"].round(1)
    summary["median_countries"] = summary["median_countries"].round(1)

    return summary


def main():
    print("Reading strict enhanced dataset...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    # Add QC flags
    df = add_active_status_flag(df)
    df = add_development_phase_flag(df)

    # -----------------------------
    # 1. Top 50 enrolment outliers
    # -----------------------------
    top_50_enrollment = (
        df
        .sort_values("enrollment_count_clean", ascending=False)
        .head(50)
    )

    top_50_enrollment = select_core_columns(top_50_enrollment)

    # -----------------------------
    # 2. Very large enrolment trials
    # -----------------------------
    very_large_trials = df[
        df["enrollment_count_clean"] > 10000
    ].sort_values("enrollment_count_clean", ascending=False)

    very_large_trials = select_core_columns(very_large_trials)

    # -----------------------------
    # 3. Active/recruiting trials
    # -----------------------------
    active_trials = df[
        df["active_trial_flag"]
    ].sort_values(["overall_status", "start_year"], ascending=[True, False])

    active_trials = select_core_columns(active_trials)

    # -----------------------------
    # 4. Phase 1–3 interventional trials
    # -----------------------------
    development_trials = df[
        df["development_relevant_flag"]
    ].sort_values(["phase_clean", "start_year"], ascending=[True, False])

    development_trials = select_core_columns(development_trials)

    # -----------------------------
    # 5. Product family × phase
    # -----------------------------
    product_family_phase = pd.crosstab(
        df["product_family_clean"],
        df["phase_clean"]
    ).reset_index()

    product_family_phase["total_trials"] = product_family_phase.drop(
        columns=["product_family_clean"]
    ).sum(axis=1)

    product_family_phase = product_family_phase.sort_values(
        "total_trials",
        ascending=False
    )

    # -----------------------------
    # 6. Product family × status
    # -----------------------------
    product_family_status = pd.crosstab(
        df["product_family_clean"],
        df["overall_status"]
    ).reset_index()

    product_family_status["total_trials"] = product_family_status.drop(
        columns=["product_family_clean"]
    ).sum(axis=1)

    product_family_status = product_family_status.sort_values(
        "total_trials",
        ascending=False
    )

    # -----------------------------
    # 7. Therapeutic area × status
    # -----------------------------
    therapeutic_area_status = pd.crosstab(
        df["therapeutic_area_clean"],
        df["overall_status"]
    ).reset_index()

    therapeutic_area_status["total_trials"] = therapeutic_area_status.drop(
        columns=["therapeutic_area_clean"]
    ).sum(axis=1)

    therapeutic_area_status = therapeutic_area_status.sort_values(
        "total_trials",
        ascending=False
    )

    # -----------------------------
    # 8. Summary tables
    # -----------------------------
    product_family_summary = create_product_family_summary(df)
    therapeutic_area_summary = create_therapeutic_area_summary(df)

    # -----------------------------
    # Save all sheets
    # -----------------------------
    sheet_dict = {
        "top_50_enrollment": top_50_enrollment,
        "enrollment_over_10000": very_large_trials,
        "active_trials": active_trials,
        "phase_1_to_3_interventional": development_trials,
        "product_family_phase": product_family_phase,
        "product_family_status": product_family_status,
        "therapeutic_area_status": therapeutic_area_status,
        "product_family_summary": product_family_summary,
        "therapeutic_area_summary": therapeutic_area_summary,
    }

    save_multi_sheet_excel(OUTPUT_FILE, sheet_dict)

    print("\n======================================")
    print("QC workbook created.")
    print(f"Saved Excel: {OUTPUT_FILE}")

    print("\nQC summary:")
    print(f"Total strict trials: {len(df)}")
    print(f"Active/recruiting trials: {df['active_trial_flag'].sum()}")
    print(f"Phase 1–3 interventional trials: {df['development_relevant_flag'].sum()}")
    print(f"Trials with enrolment > 10,000: {len(very_large_trials)}")

    print("\nTop 10 product families by active trials:")
    print(
        product_family_summary
        .sort_values("active_trials", ascending=False)
        [["product_family_clean", "trial_count", "active_trials", "development_relevant_trials"]]
        .head(10)
    )

    print("\nTop 10 therapeutic areas by active trials:")
    print(
        therapeutic_area_summary
        .sort_values("active_trials", ascending=False)
        [["therapeutic_area_clean", "trial_count", "active_trials", "development_relevant_trials"]]
        .head(10)
    )


if __name__ == "__main__":
    main()