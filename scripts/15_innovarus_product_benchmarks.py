import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEVELOPMENT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_development_subset.xlsx"

TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TABLES_DIR / "development_16_innovarus_product_benchmarks.xlsx"


# -----------------------------
# Innovarus-relevant product families
# -----------------------------
PRODUCT_FAMILIES = [
    "Leuprolide / leuprorelin depot",
    "Goserelin implant",
    "Octreotide depot",
    "Naltrexone ER",
    "Granisetron ER",
]


ACTIVE_STATUSES = [
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ACTIVE_NOT_RECRUITING",
    "ENROLLING_BY_INVITATION",
]


def split_pipe_values(value):
    if pd.isna(value):
        return []

    return [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]

def safe_excel_sheet_name(name, max_length=31):
    """
    Excel sheet names cannot contain: / \ ? * [ ] :
    and must be 31 characters or fewer.
    """
    invalid_chars = ["/", "\\", "?", "*", "[", "]", ":"]

    safe_name = str(name)

    for char in invalid_chars:
        safe_name = safe_name.replace(char, "-")

    return safe_name[:max_length]

def expand_by_country(df):
    expanded_rows = []

    for _, row in df.iterrows():
        countries = split_pipe_values(row.get("unique_countries", ""))

        if not countries:
            countries = ["Country not reported"]

        for country in countries:
            new_row = row.to_dict()
            new_row["country"] = country
            expanded_rows.append(new_row)

    return pd.DataFrame(expanded_rows)


def create_overall_product_summary(df):
    summary = (
        df
        .groupby("product_family_clean")
        .agg(
            trial_count=("nct_id", "nunique"),
            active_trials=("active_trial_flag", "sum"),
            median_enrollment=("enrollment_count_clean", "median"),
            mean_enrollment=("enrollment_count_clean", "mean"),
            min_enrollment=("enrollment_count_clean", "min"),
            max_enrollment=("enrollment_count_clean", "max"),
            median_duration_primary_months=("duration_to_primary_completion_months", "median"),
            mean_duration_primary_months=("duration_to_primary_completion_months", "mean"),
            median_duration_study_months=("duration_to_study_completion_months", "median"),
            mean_duration_study_months=("duration_to_study_completion_months", "mean"),
            median_sites=("number_of_sites", "median"),
            median_countries=("number_of_countries", "median"),
            sponsor_count=("sponsor_normalized", "nunique"),
        )
        .reset_index()
        .sort_values("trial_count", ascending=False)
    )

    numeric_cols = [
        "median_enrollment",
        "mean_enrollment",
        "median_duration_primary_months",
        "mean_duration_primary_months",
        "median_duration_study_months",
        "mean_duration_study_months",
        "median_sites",
        "median_countries",
    ]

    for col in numeric_cols:
        summary[col] = summary[col].round(1)

    return summary


def create_phase_summary(df):
    phase_summary = pd.crosstab(
        df["product_family_clean"],
        df["phase_clean"]
    ).reset_index()

    phase_summary["total_trials"] = phase_summary.drop(
        columns=["product_family_clean"]
    ).sum(axis=1)

    return phase_summary.sort_values("total_trials", ascending=False)


def create_status_summary(df):
    status_summary = pd.crosstab(
        df["product_family_clean"],
        df["overall_status"]
    ).reset_index()

    status_summary["total_trials"] = status_summary.drop(
        columns=["product_family_clean"]
    ).sum(axis=1)

    return status_summary.sort_values("total_trials", ascending=False)


def create_country_summary(expanded_df):
    country_summary = (
        expanded_df
        .groupby(["product_family_clean", "country"])
        .agg(
            trial_count=("nct_id", "nunique"),
            active_trials=("active_trial_flag", "sum"),
            median_enrollment=("enrollment_count_clean", "median"),
            median_sites=("number_of_sites", "median"),
            sponsor_count=("sponsor_normalized", "nunique"),
        )
        .reset_index()
        .sort_values(["product_family_clean", "trial_count"], ascending=[True, False])
    )

    country_summary["median_enrollment"] = country_summary["median_enrollment"].round(1)
    country_summary["median_sites"] = country_summary["median_sites"].round(1)

    return country_summary


def create_top_country_summary(country_summary):
    top_tables = []

    for product_family in PRODUCT_FAMILIES:
        product_country = country_summary[
            country_summary["product_family_clean"] == product_family
        ].copy()

        product_country = product_country.sort_values(
            "trial_count",
            ascending=False
        ).head(15)

        top_tables.append(product_country)

    return pd.concat(top_tables, ignore_index=True)


def create_sponsor_summary(df):
    sponsor_summary = (
        df
        .groupby(["product_family_clean", "sponsor_normalized"])
        .agg(
            trial_count=("nct_id", "nunique"),
            active_trials=("active_trial_flag", "sum"),
            median_enrollment=("enrollment_count_clean", "median"),
        )
        .reset_index()
        .sort_values(["product_family_clean", "trial_count"], ascending=[True, False])
    )

    sponsor_summary["median_enrollment"] = sponsor_summary["median_enrollment"].round(1)

    return sponsor_summary


def create_top_sponsor_summary(sponsor_summary):
    top_tables = []

    for product_family in PRODUCT_FAMILIES:
        product_sponsor = sponsor_summary[
            sponsor_summary["product_family_clean"] == product_family
        ].copy()

        product_sponsor = product_sponsor.sort_values(
            "trial_count",
            ascending=False
        ).head(15)

        top_tables.append(product_sponsor)

    return pd.concat(top_tables, ignore_index=True)


def select_trial_detail_columns(df):
    columns = [
        "nct_id",
        "product_family_clean",
        "therapeutic_area_clean",
        "phase_clean",
        "overall_status",
        "active_trial_flag",
        "enrollment_count_clean",
        "enrollment_type",
        "duration_to_primary_completion_months",
        "duration_to_study_completion_months",
        "start_year",
        "primary_completion_year",
        "completion_year",
        "sponsor_normalized",
        "lead_sponsor_name",
        "brief_title",
        "conditions",
        "intervention_names",
        "unique_countries",
        "number_of_sites",
        "number_of_countries",
        "matched_brand_names",
        "matched_api_names",
        "matched_search_terms",
    ]

    available_cols = [col for col in columns if col in df.columns]
    return df[available_cols].copy()


def main():
    print("Reading LAI development subset...")

    df = pd.read_excel(DEVELOPMENT_FILE)

    print(f"Input rows: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    df = df[df["product_family_clean"].isin(PRODUCT_FAMILIES)].copy()

    df["active_trial_flag"] = df["overall_status"].isin(ACTIVE_STATUSES)

    print(f"Innovarus-relevant rows: {len(df)}")
    print(f"Innovarus-relevant unique NCT IDs: {df['nct_id'].nunique()}")

    expanded_country_df = expand_by_country(df)
    expanded_country_df = expanded_country_df[
        expanded_country_df["country"] != "Country not reported"
    ].copy()

    overall_summary = create_overall_product_summary(df)
    phase_summary = create_phase_summary(df)
    status_summary = create_status_summary(df)

    country_summary = create_country_summary(expanded_country_df)
    top_country_summary = create_top_country_summary(country_summary)

    sponsor_summary = create_sponsor_summary(df)
    top_sponsor_summary = create_top_sponsor_summary(sponsor_summary)

    active_trials = select_trial_detail_columns(
        df[df["active_trial_flag"]].sort_values(
            ["product_family_clean", "start_year"],
            ascending=[True, False]
        )
    )

    trial_details = select_trial_detail_columns(
        df.sort_values(
            ["product_family_clean", "phase_clean", "start_year"],
            ascending=[True, True, False]
        )
    )

    # Product-specific detail sheets
    product_detail_sheets = {}
    for product_family in PRODUCT_FAMILIES:
        product_df = df[df["product_family_clean"] == product_family].copy()
        sheet_name = safe_excel_sheet_name(product_family)
        product_detail_sheets[sheet_name] = select_trial_detail_columns(product_df)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        overall_summary.to_excel(writer, sheet_name="overall_summary", index=False)
        phase_summary.to_excel(writer, sheet_name="phase_summary", index=False)
        status_summary.to_excel(writer, sheet_name="status_summary", index=False)
        top_country_summary.to_excel(writer, sheet_name="top_countries_by_product", index=False)
        country_summary.to_excel(writer, sheet_name="all_country_product", index=False)
        top_sponsor_summary.to_excel(writer, sheet_name="top_sponsors_by_product", index=False)
        sponsor_summary.to_excel(writer, sheet_name="all_sponsor_product", index=False)
        active_trials.to_excel(writer, sheet_name="active_trials", index=False)
        trial_details.to_excel(writer, sheet_name="trial_details", index=False)

        for sheet_name, product_df in product_detail_sheets.items():
            product_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print("\n======================================")
    print("Innovarus product benchmark workbook created.")
    print(f"Saved Excel: {OUTPUT_FILE}")

    print("\nOverall product-family benchmark:")
    print(overall_summary)

    print("\nActive trials by product family:")
    print(
        overall_summary[
            [
                "product_family_clean",
                "trial_count",
                "active_trials",
                "median_enrollment",
                "median_duration_primary_months",
                "median_sites",
                "median_countries",
            ]
        ]
    )


if __name__ == "__main__":
    main()