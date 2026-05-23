import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_relevance_scored.xlsx"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = PROCESSED_DIR / "lai_clinical_trials_cleaned.csv"
OUTPUT_XLSX = PROCESSED_DIR / "lai_clinical_trials_cleaned.xlsx"


# -----------------------------
# Helper functions
# -----------------------------
def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).lower().strip()


def classify_therapeutic_area(row):
    """
    Rule-based therapeutic area classification.

    We use conditions first, then title and matched categories.
    This is not final regulatory classification; it is an analytical grouping.
    """
    text = " ".join([
        clean_text(row.get("conditions", "")),
        clean_text(row.get("brief_title", "")),
        clean_text(row.get("official_title", "")),
        clean_text(row.get("matched_categories", "")),
        clean_text(row.get("intervention_names", "")),
    ])

    if any(term in text for term in [
        "schizophrenia", "schizoaffective", "bipolar", "psychosis", "psychotic"
    ]):
        return "Psychiatry / CNS"

    if any(term in text for term in [
        "opioid", "alcohol dependence", "substance use", "addiction", "withdrawal"
    ]):
        return "Addiction / substance use"

    if any(term in text for term in [
        "hiv", "human immunodeficiency virus", "pre-exposure prophylaxis", "prep"
    ]):
        return "HIV / infectious disease"

    if any(term in text for term in [
        "acromegaly", "neuroendocrine", "carcinoid", "vipoma", "cushing",
        "somatostatin", "octreotide", "lanreotide", "pasireotide"
    ]):
        return "Endocrinology / peptide depot"

    if any(term in text for term in [
        "prostate cancer", "breast cancer", "endometriosis", "fibroid",
        "precocious puberty", "central precocious puberty", "ovarian suppression",
        "leuprolide", "leuprorelin", "goserelin", "triptorelin", "histrelin",
        "degarelix"
    ]):
        return "GnRH / hormonal oncology"

    if any(term in text for term in [
        "contraception", "contraceptive", "medroxyprogesterone", "norethisterone",
        "norethindrone", "dmpa"
    ]):
        return "Contraception / women's health"

    if any(term in text for term in [
        "diabetes", "type 2 diabetes", "exenatide", "glucose", "glycemic"
    ]):
        return "Metabolic / diabetes"

    if any(term in text for term in [
        "postoperative pain", "post-operative pain", "postsurgical", "post-surgical",
        "analgesia", "bupivacaine", "meloxicam", "surgical site"
    ]):
        return "Pain / local analgesia"

    if any(term in text for term in [
        "osteoarthritis", "knee pain", "triamcinolone", "intra-articular", "zilretta"
    ]):
        return "Local anti-inflammatory"

    if any(term in text for term in [
        "nausea", "vomiting", "chemotherapy-induced", "granisetron", "cinv"
    ]):
        return "Supportive care / antiemetic"

    return "Other / unclassified"


def parse_date(value):
    """
    Convert ClinicalTrials.gov date strings into pandas datetime.

    ClinicalTrials.gov dates may be exact dates or month/year.
    pandas can usually parse both.
    """
    if pd.isna(value) or str(value).strip() == "":
        return pd.NaT

    return pd.to_datetime(value, errors="coerce")


def calculate_duration_months(start_date, end_date):
    if pd.isna(start_date) or pd.isna(end_date):
        return pd.NA

    days = (end_date - start_date).days

    if days < 0:
        return pd.NA

    return round(days / 30.44, 1)


def clean_phase(value):
    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return "Not specified"

    return value


def main():
    print("Reading relevance-scored dataset...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Input rows: {len(df)}")
    print("Relevance flags in input:")
    print(df["relevance_flag"].value_counts())

    # Keep analytical candidates
    keep_flags = ["High", "Medium", "Review"]
    cleaned_df = df[df["relevance_flag"].isin(keep_flags)].copy()

    print(f"\nRows kept for analysis: {len(cleaned_df)}")

    # Clean enrolment
    cleaned_df["enrollment_count_clean"] = pd.to_numeric(
        cleaned_df["enrollment_count"],
        errors="coerce"
    )

    # Clean phase
    cleaned_df["phase_clean"] = cleaned_df["phases"].apply(clean_phase)

    # Parse dates
    cleaned_df["start_date_parsed"] = cleaned_df["start_date"].apply(parse_date)
    cleaned_df["primary_completion_date_parsed"] = cleaned_df["primary_completion_date"].apply(parse_date)
    cleaned_df["completion_date_parsed"] = cleaned_df["completion_date"].apply(parse_date)

    # Years
    cleaned_df["start_year"] = cleaned_df["start_date_parsed"].dt.year
    cleaned_df["primary_completion_year"] = cleaned_df["primary_completion_date_parsed"].dt.year
    cleaned_df["completion_year"] = cleaned_df["completion_date_parsed"].dt.year

    # Duration calculations
    cleaned_df["duration_to_primary_completion_months"] = cleaned_df.apply(
        lambda row: calculate_duration_months(
            row["start_date_parsed"],
            row["primary_completion_date_parsed"]
        ),
        axis=1
    )

    cleaned_df["duration_to_study_completion_months"] = cleaned_df.apply(
        lambda row: calculate_duration_months(
            row["start_date_parsed"],
            row["completion_date_parsed"]
        ),
        axis=1
    )

    # Therapeutic area
    cleaned_df["therapeutic_area_clean"] = cleaned_df.apply(
        classify_therapeutic_area,
        axis=1
    )

    # Put important analytical columns first
    first_columns = [
        "nct_id",
        "relevance_flag",
        "relevance_score",
        "therapeutic_area_clean",
        "phase_clean",
        "overall_status",
        "enrollment_count_clean",
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

    remaining_columns = [col for col in cleaned_df.columns if col not in first_columns]
    cleaned_df = cleaned_df[first_columns + remaining_columns]

    # Save
    cleaned_df.to_csv(OUTPUT_CSV, index=False)
    cleaned_df.to_excel(OUTPUT_XLSX, index=False)

    print("\n======================================")
    print("Cleaned analysis dataset created.")
    print(f"Rows saved: {len(cleaned_df)}")
    print(f"Unique NCT IDs: {cleaned_df['nct_id'].nunique()}")
    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved Excel: {OUTPUT_XLSX}")

    print("\nTherapeutic area counts:")
    print(cleaned_df["therapeutic_area_clean"].value_counts())

    print("\nPhase counts:")
    print(cleaned_df["phase_clean"].value_counts())

    print("\nStatus counts:")
    print(cleaned_df["overall_status"].value_counts())


if __name__ == "__main__":
    main()