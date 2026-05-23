import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_strict_enhanced.xlsx"

FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Helper functions
# -----------------------------
def shorten_label(value, max_words=4):
    """
    Shorten long labels to a maximum number of words.
    Useful for sponsor names and long product labels in plots.
    """
    if pd.isna(value):
        return ""

    words = str(value).split()

    if len(words) <= max_words:
        return str(value)

    return " ".join(words[:max_words]) + "..."


def save_bar_chart(series, title, xlabel, ylabel, output_filename, horizontal=False, figsize=(10, 6)):
    """
    Save a simple bar chart from a pandas Series.
    """
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


def save_table(df, filename):
    """
    Save a dataframe to Excel in the reports/tables folder.
    """
    output_path = TABLES_DIR / filename
    df.to_excel(output_path, index=False)
    print(f"Saved table: {output_path}")


def split_pipe_column_to_counts(df, column_name):
    """
    For columns like 'United States | Canada | Germany',
    split values and count each individual item.
    """
    all_items = []

    for value in df[column_name].dropna():
        items = [item.strip() for item in str(value).split("|") if item.strip()]
        all_items.extend(items)

    return pd.Series(all_items).value_counts()


def create_enrollment_summary(df, group_column):
    """
    Create enrolment summary by a grouping column.
    """
    summary = (
        df
        .groupby(group_column)["enrollment_count_clean"]
        .agg(
            trial_count="count",
            total_enrollment="sum",
            mean_enrollment="mean",
            median_enrollment="median",
            min_enrollment="min",
            max_enrollment="max"
        )
        .reset_index()
    )

    summary["mean_enrollment"] = summary["mean_enrollment"].round(1)
    summary["median_enrollment"] = summary["median_enrollment"].round(1)

    return summary.sort_values("trial_count", ascending=False)


def main():
    print("Reading strict enhanced LAI clinical trials dataset...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    # -----------------------------
    # 1. Trial count by therapeutic area
    # -----------------------------
    therapeutic_counts = df["therapeutic_area_clean"].value_counts()

    save_bar_chart(
        therapeutic_counts,
        title="Strict LAI Clinical Trials by Therapeutic Area",
        xlabel="Number of trials",
        ylabel="Therapeutic area",
        output_filename="strict_01_trials_by_therapeutic_area.png",
        horizontal=True,
        figsize=(10, 6)
    )

    save_table(
        therapeutic_counts.reset_index().rename(
            columns={
                "therapeutic_area_clean": "therapeutic_area",
                "count": "trial_count"
            }
        ),
        "strict_01_trials_by_therapeutic_area.xlsx"
    )

    # -----------------------------
    # 2. Trial count by product family
    # -----------------------------
    product_family_counts = df["product_family_clean"].value_counts().head(25)

    product_family_plot = pd.Series(
        product_family_counts.values,
        index=[shorten_label(label, max_words=5) for label in product_family_counts.index]
    )

    save_bar_chart(
        product_family_plot,
        title="Top LAI Product Families by Clinical Trial Count",
        xlabel="Number of trials",
        ylabel="Product family",
        output_filename="strict_02_trials_by_product_family.png",
        horizontal=True,
        figsize=(11, 8)
    )

    save_table(
        product_family_counts.reset_index().rename(
            columns={
                "product_family_clean": "product_family",
                "count": "trial_count"
            }
        ),
        "strict_02_trials_by_product_family.xlsx"
    )

    # -----------------------------
    # 3. Trial count by phase
    # -----------------------------
    phase_order = [
        "EARLY_PHASE1",
        "PHASE1",
        "PHASE1 | PHASE2",
        "PHASE2",
        "PHASE2 | PHASE3",
        "PHASE3",
        "PHASE4",
        "Not specified"
    ]

    phase_counts = df["phase_clean"].value_counts()
    phase_counts = phase_counts.reindex(
        [phase for phase in phase_order if phase in phase_counts.index]
    )

    save_bar_chart(
        phase_counts,
        title="Strict LAI Clinical Trials by Phase",
        xlabel="Clinical phase",
        ylabel="Number of trials",
        output_filename="strict_03_trials_by_phase.png",
        horizontal=False,
        figsize=(10, 6)
    )

    save_table(
        phase_counts.reset_index().rename(
            columns={
                "phase_clean": "phase",
                "count": "trial_count"
            }
        ),
        "strict_03_trials_by_phase.xlsx"
    )

    # -----------------------------
    # 4. Trial count by status
    # -----------------------------
    status_counts = df["overall_status"].value_counts()

    status_plot = pd.Series(
        status_counts.values,
        index=[shorten_label(label.replace("_", " "), max_words=3) for label in status_counts.index]
    )

    save_bar_chart(
        status_plot,
        title="Strict LAI Clinical Trials by Study Status",
        xlabel="Number of trials",
        ylabel="Study status",
        output_filename="strict_04_trials_by_status.png",
        horizontal=True,
        figsize=(10, 6)
    )

    save_table(
        status_counts.reset_index().rename(
            columns={
                "overall_status": "status",
                "count": "trial_count"
            }
        ),
        "strict_04_trials_by_status.xlsx"
    )

    # -----------------------------
    # 5. Trial start-year trend
    # -----------------------------
    start_year_counts = (
        df
        .dropna(subset=["start_year"])
        .assign(start_year=lambda x: x["start_year"].astype(int))
        .groupby("start_year")
        .size()
    )

    save_bar_chart(
        start_year_counts,
        title="Strict LAI Clinical Trials by Start Year",
        xlabel="Start year",
        ylabel="Number of trials",
        output_filename="strict_05_trials_by_start_year.png",
        horizontal=False,
        figsize=(13, 6)
    )

    save_table(
        start_year_counts.reset_index().rename(
            columns={
                0: "trial_count"
            }
        ),
        "strict_05_trials_by_start_year.xlsx"
    )

    # -----------------------------
    # 6. Top normalised sponsors
    # -----------------------------
    top_sponsors = df["sponsor_normalized"].value_counts().head(20)

    sponsor_plot = pd.Series(
        top_sponsors.values,
        index=[shorten_label(sponsor, max_words=4) for sponsor in top_sponsors.index]
    )

    save_bar_chart(
        sponsor_plot,
        title="Top 20 Normalised LAI Clinical Trial Sponsors",
        xlabel="Number of trials",
        ylabel="Sponsor",
        output_filename="strict_06_top_20_normalized_sponsors.png",
        horizontal=True,
        figsize=(11, 7)
    )

    save_table(
        top_sponsors.reset_index().rename(
            columns={
                "sponsor_normalized": "sponsor_normalized",
                "count": "trial_count"
            }
        ),
        "strict_06_top_20_normalized_sponsors.xlsx"
    )

    # -----------------------------
    # 7. Top countries
    # -----------------------------
    country_counts = split_pipe_column_to_counts(df, "unique_countries").head(25)

    save_bar_chart(
        country_counts,
        title="Top 25 Countries in Strict LAI Clinical Trials",
        xlabel="Number of trials",
        ylabel="Country",
        output_filename="strict_07_top_25_countries.png",
        horizontal=True,
        figsize=(10, 8)
    )

    save_table(
        country_counts.reset_index().rename(
            columns={
                "index": "country",
                "count": "trial_count"
            }
        ),
        "strict_07_top_25_countries.xlsx"
    )

    # -----------------------------
    # 8. Enrolment summary by phase
    # -----------------------------
    enrollment_by_phase = create_enrollment_summary(df, "phase_clean")

    save_table(
        enrollment_by_phase,
        "strict_08_enrollment_summary_by_phase.xlsx"
    )

    median_enrollment_phase = (
        enrollment_by_phase
        .set_index("phase_clean")["median_enrollment"]
        .dropna()
    )

    save_bar_chart(
        median_enrollment_phase,
        title="Strict Dataset: Median Enrolment by Clinical Phase",
        xlabel="Clinical phase",
        ylabel="Median enrolment",
        output_filename="strict_08_median_enrollment_by_phase.png",
        horizontal=False,
        figsize=(10, 6)
    )

    # -----------------------------
    # 9. Enrolment summary by therapeutic area
    # -----------------------------
    enrollment_by_area = create_enrollment_summary(df, "therapeutic_area_clean")

    save_table(
        enrollment_by_area,
        "strict_09_enrollment_summary_by_therapeutic_area.xlsx"
    )

    median_enrollment_area = (
        enrollment_by_area
        .set_index("therapeutic_area_clean")["median_enrollment"]
        .dropna()
    )

    save_bar_chart(
        median_enrollment_area,
        title="Strict Dataset: Median Enrolment by Therapeutic Area",
        xlabel="Median enrolment",
        ylabel="Therapeutic area",
        output_filename="strict_09_median_enrollment_by_therapeutic_area.png",
        horizontal=True,
        figsize=(10, 6)
    )

    # -----------------------------
    # 10. Enrolment summary by product family
    # -----------------------------
    enrollment_by_product_family = create_enrollment_summary(df, "product_family_clean")

    save_table(
        enrollment_by_product_family,
        "strict_10_enrollment_summary_by_product_family.xlsx"
    )

    top_product_family_enrollment = (
        enrollment_by_product_family
        .sort_values("trial_count", ascending=False)
        .head(20)
        .set_index("product_family_clean")["median_enrollment"]
        .dropna()
    )

    product_family_enrollment_plot = pd.Series(
        top_product_family_enrollment.values,
        index=[shorten_label(label, max_words=5) for label in top_product_family_enrollment.index]
    )

    save_bar_chart(
        product_family_enrollment_plot,
        title="Median Enrolment by Top LAI Product Families",
        xlabel="Median enrolment",
        ylabel="Product family",
        output_filename="strict_10_median_enrollment_by_product_family.png",
        horizontal=True,
        figsize=(11, 8)
    )

    # -----------------------------
    # 11. Therapeutic area by phase crosstab
    # -----------------------------
    area_phase_table = pd.crosstab(
        df["therapeutic_area_clean"],
        df["phase_clean"]
    ).reset_index()

    save_table(
        area_phase_table,
        "strict_11_therapeutic_area_by_phase_crosstab.xlsx"
    )

    # -----------------------------
    # 12. Product family by phase crosstab
    # -----------------------------
    product_family_phase_table = pd.crosstab(
        df["product_family_clean"],
        df["phase_clean"]
    ).reset_index()

    save_table(
        product_family_phase_table,
        "strict_12_product_family_by_phase_crosstab.xlsx"
    )

    # -----------------------------
    # 13. Product family by therapeutic area
    # -----------------------------
    product_family_area_table = pd.crosstab(
        df["product_family_clean"],
        df["therapeutic_area_clean"]
    ).reset_index()

    save_table(
        product_family_area_table,
        "strict_13_product_family_by_therapeutic_area_crosstab.xlsx"
    )

    print("\n======================================")
    print("Strict enhanced EDA complete.")
    print(f"Figures saved in: {FIGURES_DIR}")
    print(f"Tables saved in: {TABLES_DIR}")

    print("\nQuick strict dataset summary:")
    print(f"Total trials: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")
    print(f"Therapeutic areas: {df['therapeutic_area_clean'].nunique()}")
    print(f"Product families: {df['product_family_clean'].nunique()}")
    print(f"Countries represented: {split_pipe_column_to_counts(df, 'unique_countries').shape[0]}")
    print(f"Median enrolment overall: {df['enrollment_count_clean'].median()}")
    print(f"Mean enrolment overall: {round(df['enrollment_count_clean'].mean(), 1)}")


if __name__ == "__main__":
    main()