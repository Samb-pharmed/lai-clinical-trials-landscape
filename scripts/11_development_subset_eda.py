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


# -----------------------------
# Helper functions
# -----------------------------
def shorten_label(value, max_words=5):
    if pd.isna(value):
        return ""

    words = str(value).split()

    if len(words) <= max_words:
        return str(value)

    return " ".join(words[:max_words]) + "..."


def save_bar_chart(series, title, xlabel, ylabel, output_filename, horizontal=False, figsize=(10, 6)):
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
    output_path = TABLES_DIR / filename
    df.to_excel(output_path, index=False)
    print(f"Saved table: {output_path}")


def split_pipe_column_to_counts(df, column_name):
    all_items = []

    for value in df[column_name].dropna():
        items = [item.strip() for item in str(value).split("|") if item.strip()]
        all_items.extend(items)

    if not all_items:
        return pd.Series(dtype="int64")

    return pd.Series(all_items).value_counts()


def create_enrollment_summary(df, group_column):
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


def create_duration_summary(df, group_column):
    summary = (
        df
        .groupby(group_column)
        .agg(
            trial_count=("nct_id", "count"),
            median_duration_primary_months=("duration_to_primary_completion_months", "median"),
            mean_duration_primary_months=("duration_to_primary_completion_months", "mean"),
            median_duration_study_months=("duration_to_study_completion_months", "median"),
            mean_duration_study_months=("duration_to_study_completion_months", "mean"),
        )
        .reset_index()
    )

    for col in [
        "median_duration_primary_months",
        "mean_duration_primary_months",
        "median_duration_study_months",
        "mean_duration_study_months",
    ]:
        summary[col] = summary[col].round(1)

    return summary.sort_values("trial_count", ascending=False)


def main():
    print("Reading LAI development subset...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    # -----------------------------
    # 1. Development trials by phase
    # -----------------------------
    phase_order = [
        "EARLY_PHASE1",
        "PHASE1",
        "PHASE1 | PHASE2",
        "PHASE2",
        "PHASE2 | PHASE3",
        "PHASE3",
    ]

    phase_counts = df["phase_clean"].value_counts()
    phase_counts = phase_counts.reindex(
        [phase for phase in phase_order if phase in phase_counts.index]
    )

    save_bar_chart(
        phase_counts,
        title="LAI Development Trials by Phase",
        xlabel="Clinical phase",
        ylabel="Number of trials",
        output_filename="development_01_trials_by_phase.png",
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
        "development_01_trials_by_phase.xlsx"
    )

    # -----------------------------
    # 2. Development trials by therapeutic area
    # -----------------------------
    therapeutic_counts = df["therapeutic_area_clean"].value_counts()

    save_bar_chart(
        therapeutic_counts,
        title="LAI Development Trials by Therapeutic Area",
        xlabel="Number of trials",
        ylabel="Therapeutic area",
        output_filename="development_02_trials_by_therapeutic_area.png",
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
        "development_02_trials_by_therapeutic_area.xlsx"
    )

    # -----------------------------
    # 3. Development trials by product family
    # -----------------------------
    product_counts = df["product_family_clean"].value_counts().head(25)

    product_plot = pd.Series(
        product_counts.values,
        index=[shorten_label(label, max_words=5) for label in product_counts.index]
    )

    save_bar_chart(
        product_plot,
        title="Top LAI Product Families in Phase 1–3 Development",
        xlabel="Number of trials",
        ylabel="Product family",
        output_filename="development_03_trials_by_product_family.png",
        horizontal=True,
        figsize=(11, 8)
    )

    save_table(
        product_counts.reset_index().rename(
            columns={
                "product_family_clean": "product_family",
                "count": "trial_count"
            }
        ),
        "development_03_trials_by_product_family.xlsx"
    )

    # -----------------------------
    # 4. Median enrolment by phase
    # -----------------------------
    enrollment_by_phase = create_enrollment_summary(df, "phase_clean")
    save_table(enrollment_by_phase, "development_04_enrollment_summary_by_phase.xlsx")

    median_enrollment_phase = (
        enrollment_by_phase
        .set_index("phase_clean")
        .reindex([phase for phase in phase_order if phase in enrollment_by_phase["phase_clean"].values])
        ["median_enrollment"]
        .dropna()
    )

    save_bar_chart(
        median_enrollment_phase,
        title="Median Enrolment by Phase in LAI Development Trials",
        xlabel="Clinical phase",
        ylabel="Median enrolment",
        output_filename="development_04_median_enrollment_by_phase.png",
        horizontal=False,
        figsize=(10, 6)
    )

    # -----------------------------
    # 5. Median enrolment by product family
    # -----------------------------
    enrollment_by_product = create_enrollment_summary(df, "product_family_clean")
    save_table(enrollment_by_product, "development_05_enrollment_summary_by_product_family.xlsx")

    top_product_enrollment = (
        enrollment_by_product
        .sort_values("trial_count", ascending=False)
        .head(20)
        .set_index("product_family_clean")["median_enrollment"]
        .dropna()
    )

    top_product_enrollment_plot = pd.Series(
        top_product_enrollment.values,
        index=[shorten_label(label, max_words=5) for label in top_product_enrollment.index]
    )

    save_bar_chart(
        top_product_enrollment_plot,
        title="Median Enrolment by Product Family in LAI Development Trials",
        xlabel="Median enrolment",
        ylabel="Product family",
        output_filename="development_05_median_enrollment_by_product_family.png",
        horizontal=True,
        figsize=(11, 8)
    )

    # -----------------------------
    # 6. Median enrolment by therapeutic area
    # -----------------------------
    enrollment_by_area = create_enrollment_summary(df, "therapeutic_area_clean")
    save_table(enrollment_by_area, "development_06_enrollment_summary_by_therapeutic_area.xlsx")

    median_enrollment_area = (
        enrollment_by_area
        .set_index("therapeutic_area_clean")["median_enrollment"]
        .dropna()
    )

    save_bar_chart(
        median_enrollment_area,
        title="Median Enrolment by Therapeutic Area in LAI Development Trials",
        xlabel="Median enrolment",
        ylabel="Therapeutic area",
        output_filename="development_06_median_enrollment_by_therapeutic_area.png",
        horizontal=True,
        figsize=(10, 6)
    )

    # -----------------------------
    # 7. Duration by phase
    # -----------------------------
    duration_by_phase = create_duration_summary(df, "phase_clean")
    save_table(duration_by_phase, "development_07_duration_summary_by_phase.xlsx")

    median_duration_phase = (
        duration_by_phase
        .set_index("phase_clean")
        .reindex([phase for phase in phase_order if phase in duration_by_phase["phase_clean"].values])
        ["median_duration_primary_months"]
        .dropna()
    )

    save_bar_chart(
        median_duration_phase,
        title="Median Duration to Primary Completion by Phase",
        xlabel="Clinical phase",
        ylabel="Median duration, months",
        output_filename="development_07_median_duration_by_phase.png",
        horizontal=False,
        figsize=(10, 6)
    )

    # -----------------------------
    # 8. Duration by product family
    # -----------------------------
    duration_by_product = create_duration_summary(df, "product_family_clean")
    save_table(duration_by_product, "development_08_duration_summary_by_product_family.xlsx")

    top_product_duration = (
        duration_by_product
        .sort_values("trial_count", ascending=False)
        .head(20)
        .set_index("product_family_clean")["median_duration_primary_months"]
        .dropna()
    )

    top_product_duration_plot = pd.Series(
        top_product_duration.values,
        index=[shorten_label(label, max_words=5) for label in top_product_duration.index]
    )

    save_bar_chart(
        top_product_duration_plot,
        title="Median Duration to Primary Completion by Product Family",
        xlabel="Median duration, months",
        ylabel="Product family",
        output_filename="development_08_median_duration_by_product_family.png",
        horizontal=True,
        figsize=(11, 8)
    )

    # -----------------------------
    # 9. Top development sponsors
    # -----------------------------
    top_sponsors = df["sponsor_normalized"].value_counts().head(20)

    sponsor_plot = pd.Series(
        top_sponsors.values,
        index=[shorten_label(label, max_words=4) for label in top_sponsors.index]
    )

    save_bar_chart(
        sponsor_plot,
        title="Top Sponsors in LAI Phase 1–3 Development Trials",
        xlabel="Number of trials",
        ylabel="Sponsor",
        output_filename="development_09_top_sponsors.png",
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
        "development_09_top_sponsors.xlsx"
    )

    # -----------------------------
    # 10. Top countries in development trials
    # -----------------------------
    country_counts = split_pipe_column_to_counts(df, "unique_countries").head(25)

    save_bar_chart(
        country_counts,
        title="Top Countries in LAI Phase 1–3 Development Trials",
        xlabel="Number of trials",
        ylabel="Country",
        output_filename="development_10_top_countries.png",
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
        "development_10_top_countries.xlsx"
    )

    # -----------------------------
    # 11. Product family × phase
    # -----------------------------
    product_phase_table = pd.crosstab(
        df["product_family_clean"],
        df["phase_clean"]
    ).reset_index()

    product_phase_table["total_trials"] = product_phase_table.drop(
        columns=["product_family_clean"]
    ).sum(axis=1)

    product_phase_table = product_phase_table.sort_values("total_trials", ascending=False)

    save_table(product_phase_table, "development_11_product_family_by_phase.xlsx")

    # -----------------------------
    # 12. Therapeutic area × phase
    # -----------------------------
    area_phase_table = pd.crosstab(
        df["therapeutic_area_clean"],
        df["phase_clean"]
    ).reset_index()

    area_phase_table["total_trials"] = area_phase_table.drop(
        columns=["therapeutic_area_clean"]
    ).sum(axis=1)

    area_phase_table = area_phase_table.sort_values("total_trials", ascending=False)

    save_table(area_phase_table, "development_12_therapeutic_area_by_phase.xlsx")

    print("\n======================================")
    print("Development subset EDA complete.")
    print(f"Figures saved in: {FIGURES_DIR}")
    print(f"Tables saved in: {TABLES_DIR}")

    print("\nQuick development subset summary:")
    print(f"Total development trials: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")
    print(f"Therapeutic areas: {df['therapeutic_area_clean'].nunique()}")
    print(f"Product families: {df['product_family_clean'].nunique()}")
    print(f"Countries represented: {split_pipe_column_to_counts(df, 'unique_countries').shape[0]}")
    print(f"Median enrolment overall: {df['enrollment_count_clean'].median()}")
    print(f"Mean enrolment overall: {round(df['enrollment_count_clean'].mean(), 1)}")
    print(f"Median duration to primary completion: {df['duration_to_primary_completion_months'].median()} months")


if __name__ == "__main__":
    main()