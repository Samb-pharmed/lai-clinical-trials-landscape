import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_development_subset.xlsx"

FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_COUNTRY_SUMMARY = TABLES_DIR / "development_13_country_summary.xlsx"
OUTPUT_COUNTRY_TRIALS = TABLES_DIR / "development_14_country_trial_level_expanded.xlsx"


# -----------------------------
# Helper functions
# -----------------------------
def split_pipe_values(value):
    if pd.isna(value):
        return []

    return [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]


def save_table(df, filename):
    output_path = TABLES_DIR / filename
    df.to_excel(output_path, index=False)
    print(f"Saved table: {output_path}")


def save_bar_chart(series, title, xlabel, ylabel, output_filename, horizontal=True, figsize=(10, 8)):
    plt.figure(figsize=figsize)

    if horizontal:
        series.sort_values().plot(kind="barh")
    else:
        series.plot(kind="bar")

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()

    output_path = FIGURES_DIR / output_filename
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved figure: {output_path}")


def add_active_flag(df):
    active_statuses = [
        "RECRUITING",
        "NOT_YET_RECRUITING",
        "ACTIVE_NOT_RECRUITING",
        "ENROLLING_BY_INVITATION",
    ]

    df = df.copy()
    df["active_trial_flag"] = df["overall_status"].isin(active_statuses)
    return df


def expand_trials_by_country(df):
    """
    Convert one trial with multiple countries into multiple rows:
    one row per NCT ID per country.

    Example:
    NCT001: United States | Canada
    becomes:
    NCT001 - United States
    NCT001 - Canada
    """
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


def create_country_summary(country_trial_df):
    """
    Build country-level recruitment/development summary.
    """
    summary = (
        country_trial_df
        .groupby("country")
        .agg(
            trial_count=("nct_id", "nunique"),
            active_trial_count=("active_trial_flag", "sum"),
            total_enrollment=("enrollment_count_clean", "sum"),
            median_enrollment=("enrollment_count_clean", "median"),
            mean_enrollment=("enrollment_count_clean", "mean"),
            median_sites_per_trial=("number_of_sites", "median"),
            median_countries_per_trial=("number_of_countries", "median"),
            product_family_count=("product_family_clean", "nunique"),
            therapeutic_area_count=("therapeutic_area_clean", "nunique"),
            sponsor_count=("sponsor_normalized", "nunique"),
        )
        .reset_index()
    )

    summary["mean_enrollment"] = summary["mean_enrollment"].round(1)
    summary["median_enrollment"] = summary["median_enrollment"].round(1)
    summary["median_sites_per_trial"] = summary["median_sites_per_trial"].round(1)
    summary["median_countries_per_trial"] = summary["median_countries_per_trial"].round(1)

    # Simple recruitment/development attractiveness score.
    # This is not a final model. It is a transparent business-rule score.
    summary["country_development_score"] = (
        summary["trial_count"].rank(pct=True) * 0.30
        + summary["active_trial_count"].rank(pct=True) * 0.25
        + summary["product_family_count"].rank(pct=True) * 0.20
        + summary["sponsor_count"].rank(pct=True) * 0.15
        + summary["therapeutic_area_count"].rank(pct=True) * 0.10
    )

    summary["country_development_score"] = (
        summary["country_development_score"] * 100
    ).round(1)

    return summary.sort_values("trial_count", ascending=False)


def main():
    print("Reading LAI development subset...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Input rows: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    df = add_active_flag(df)

    print("\nExpanding trial records by country...")
    country_trial_df = expand_trials_by_country(df)

    print(f"Expanded country-trial rows: {len(country_trial_df)}")
    print(f"Countries represented: {country_trial_df['country'].nunique()}")

    country_summary = create_country_summary(country_trial_df)

    # Save country-level outputs
    country_summary.to_excel(OUTPUT_COUNTRY_SUMMARY, index=False)
    country_trial_df.to_excel(OUTPUT_COUNTRY_TRIALS, index=False)

    print(f"Saved country summary: {OUTPUT_COUNTRY_SUMMARY}")
    print(f"Saved expanded trial-country table: {OUTPUT_COUNTRY_TRIALS}")

    # -----------------------------
    # Charts
    # -----------------------------
    top_trial_count = (
        country_summary
        .set_index("country")["trial_count"]
        .head(25)
    )

    save_bar_chart(
        top_trial_count,
        title="Top Countries by LAI Phase 1–3 Development Trial Count",
        xlabel="Number of development trials",
        ylabel="Country",
        output_filename="development_11_top_countries_by_trial_count.png",
        horizontal=True,
        figsize=(10, 8)
    )

    top_active = (
        country_summary
        .sort_values("active_trial_count", ascending=False)
        .head(25)
        .set_index("country")["active_trial_count"]
    )

    save_bar_chart(
        top_active,
        title="Top Countries by Active LAI Development Trials",
        xlabel="Number of active development trials",
        ylabel="Country",
        output_filename="development_12_top_countries_by_active_trials.png",
        horizontal=True,
        figsize=(10, 8)
    )

    top_product_diversity = (
        country_summary
        .sort_values("product_family_count", ascending=False)
        .head(25)
        .set_index("country")["product_family_count"]
    )

    save_bar_chart(
        top_product_diversity,
        title="Top Countries by LAI Product Family Diversity",
        xlabel="Number of product families represented",
        ylabel="Country",
        output_filename="development_13_top_countries_by_product_family_diversity.png",
        horizontal=True,
        figsize=(10, 8)
    )

    top_score = (
        country_summary
        .sort_values("country_development_score", ascending=False)
        .head(25)
        .set_index("country")["country_development_score"]
    )

    save_bar_chart(
        top_score,
        title="Top Countries by LAI Development Activity Score",
        xlabel="Development activity score",
        ylabel="Country",
        output_filename="development_14_top_countries_by_development_score.png",
        horizontal=True,
        figsize=(10, 8)
    )

    print("\n======================================")
    print("Development geography analysis complete.")

    print("\nTop 20 countries by trial count:")
    print(
        country_summary[
            [
                "country",
                "trial_count",
                "active_trial_count",
                "product_family_count",
                "therapeutic_area_count",
                "sponsor_count",
                "country_development_score",
            ]
        ].head(20)
    )

    print("\nTop 20 countries by active development trials:")
    print(
        country_summary
        .sort_values("active_trial_count", ascending=False)
        [
            [
                "country",
                "trial_count",
                "active_trial_count",
                "product_family_count",
                "therapeutic_area_count",
                "sponsor_count",
                "country_development_score",
            ]
        ]
        .head(20)
    )


if __name__ == "__main__":
    main()