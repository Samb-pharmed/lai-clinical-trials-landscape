import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

COUNTRY_SUMMARY_FILE = PROJECT_ROOT / "reports" / "tables" / "development_13_country_summary.xlsx"
COUNTRY_TRIAL_FILE = PROJECT_ROOT / "reports" / "tables" / "development_14_country_trial_level_expanded.xlsx"

TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
OUTPUT_FILE = TABLES_DIR / "development_15_country_strategy_summary.xlsx"


# -----------------------------
# Innovarus-relevant product families
# -----------------------------
INNOVARUS_RELEVANT_FAMILIES = [
    "Leuprolide / leuprorelin depot",
    "Goserelin implant",
    "Octreotide depot",
    "Naltrexone ER",
    "Granisetron ER",
]


def classify_country_tier(score):
    """
    Classify countries using the existing country development score.
    """
    if score >= 95:
        return "Tier 1 - Highest LAI development activity"
    if score >= 85:
        return "Tier 2 - Strong LAI development activity"
    if score >= 70:
        return "Tier 3 - Moderate LAI development activity"
    return "Tier 4 - Lower recorded activity"


def classify_country_role(row):
    """
    Strategic interpretation of country role.
    """
    trial_count = row["trial_count"]
    active_trials = row["active_trial_count"]
    product_families = row["product_family_count"]
    therapeutic_areas = row["therapeutic_area_count"]

    if trial_count >= 100 and active_trials >= 20 and product_families >= 15:
        return "Core high-activity development geography"

    if trial_count >= 80 and product_families >= 15:
        return "Broad historical LAI development geography"

    if active_trials >= 15:
        return "Current active development hotspot"

    if product_families >= 15:
        return "Broad product-family experience geography"

    if trial_count >= 40:
        return "Established secondary geography"

    return "Emerging or limited-record geography"


def create_innovarus_country_summary(country_trial_df):
    """
    Create country summary restricted to Innovarus-relevant product families.
    """
    innovarus_df = country_trial_df[
        country_trial_df["product_family_clean"].isin(INNOVARUS_RELEVANT_FAMILIES)
    ].copy()

    summary = (
        innovarus_df
        .groupby("country")
        .agg(
            innovarus_relevant_trial_count=("nct_id", "nunique"),
            innovarus_relevant_active_trials=("active_trial_flag", "sum"),
            innovarus_relevant_product_families=("product_family_clean", "nunique"),
            median_enrollment=("enrollment_count_clean", "median"),
            median_sites_per_trial=("number_of_sites", "median"),
            sponsor_count=("sponsor_normalized", "nunique"),
        )
        .reset_index()
    )

    summary["median_enrollment"] = summary["median_enrollment"].round(1)
    summary["median_sites_per_trial"] = summary["median_sites_per_trial"].round(1)

    return summary.sort_values("innovarus_relevant_trial_count", ascending=False)


def create_product_family_country_matrix(country_trial_df):
    """
    Matrix of product family presence by country.
    """
    matrix = pd.crosstab(
        country_trial_df["country"],
        country_trial_df["product_family_clean"]
    ).reset_index()

    matrix["total_trials"] = matrix.drop(columns=["country"]).sum(axis=1)

    return matrix.sort_values("total_trials", ascending=False)


def create_active_product_family_country_matrix(country_trial_df):
    """
    Matrix of active trials by country and product family.
    """
    active_df = country_trial_df[country_trial_df["active_trial_flag"]].copy()

    matrix = pd.crosstab(
        active_df["country"],
        active_df["product_family_clean"]
    ).reset_index()

    matrix["total_active_trials"] = matrix.drop(columns=["country"]).sum(axis=1)

    return matrix.sort_values("total_active_trials", ascending=False)


def main():
    print("Reading country-level geography outputs...")

    country_summary = pd.read_excel(COUNTRY_SUMMARY_FILE)
    country_trial_df = pd.read_excel(COUNTRY_TRIAL_FILE)

    print(f"Country summary rows: {len(country_summary)}")
    print(f"Expanded trial-country rows: {len(country_trial_df)}")

    # Exclude placeholder geography from strategic rankings
    country_summary_real = country_summary[
        country_summary["country"] != "Country not reported"
    ].copy()

    country_trial_real = country_trial_df[
        country_trial_df["country"] != "Country not reported"
    ].copy()

    # Add strategic classifications
    country_summary_real["country_tier"] = country_summary_real["country_development_score"].apply(
        classify_country_tier
    )

    country_summary_real["country_role"] = country_summary_real.apply(
        classify_country_role,
        axis=1
    )

    # Strategic top tables
    top_by_score = country_summary_real.sort_values(
        "country_development_score",
        ascending=False
    ).head(25)

    top_by_active = country_summary_real.sort_values(
        "active_trial_count",
        ascending=False
    ).head(25)

    top_by_product_diversity = country_summary_real.sort_values(
        "product_family_count",
        ascending=False
    ).head(25)

    top_by_sponsor_diversity = country_summary_real.sort_values(
        "sponsor_count",
        ascending=False
    ).head(25)

    # Innovarus-specific geography table
    innovarus_country_summary = create_innovarus_country_summary(country_trial_real)

    # Product family × country matrices
    product_family_country_matrix = create_product_family_country_matrix(country_trial_real)
    active_product_family_country_matrix = create_active_product_family_country_matrix(country_trial_real)

    # Tier summary
    tier_summary = (
        country_summary_real
        .groupby(["country_tier", "country_role"])
        .agg(
            country_count=("country", "count"),
            total_trials=("trial_count", "sum"),
            total_active_trials=("active_trial_count", "sum"),
            median_score=("country_development_score", "median"),
        )
        .reset_index()
        .sort_values(["country_tier", "total_trials"], ascending=[True, False])
    )

    tier_summary["median_score"] = tier_summary["median_score"].round(1)

    # Save workbook
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        country_summary_real.to_excel(writer, sheet_name="all_countries_scored", index=False)
        top_by_score.to_excel(writer, sheet_name="top_by_score", index=False)
        top_by_active.to_excel(writer, sheet_name="top_by_active", index=False)
        top_by_product_diversity.to_excel(writer, sheet_name="top_by_product_diversity", index=False)
        top_by_sponsor_diversity.to_excel(writer, sheet_name="top_by_sponsor_diversity", index=False)
        innovarus_country_summary.to_excel(writer, sheet_name="innovarus_relevant", index=False)
        product_family_country_matrix.to_excel(writer, sheet_name="product_family_country", index=False)
        active_product_family_country_matrix.to_excel(writer, sheet_name="active_family_country", index=False)
        tier_summary.to_excel(writer, sheet_name="tier_summary", index=False)

    print("\n======================================")
    print("Country strategy workbook created.")
    print(f"Saved Excel: {OUTPUT_FILE}")

    print("\nTop 15 countries by LAI development score:")
    print(
        top_by_score[
            [
                "country",
                "trial_count",
                "active_trial_count",
                "product_family_count",
                "therapeutic_area_count",
                "sponsor_count",
                "country_development_score",
                "country_tier",
                "country_role",
            ]
        ].head(15)
    )

    print("\nTop 15 Innovarus-relevant countries:")
    print(
        innovarus_country_summary[
            [
                "country",
                "innovarus_relevant_trial_count",
                "innovarus_relevant_active_trials",
                "innovarus_relevant_product_families",
                "median_enrollment",
                "median_sites_per_trial",
                "sponsor_count",
            ]
        ].head(15)
    )


if __name__ == "__main__":
    main()