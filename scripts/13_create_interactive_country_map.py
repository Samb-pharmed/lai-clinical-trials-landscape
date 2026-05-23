import pandas as pd
import plotly.express as px
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "reports" / "tables" / "development_13_country_summary.xlsx"

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_HTML_SCORE = REPORTS_DIR / "development_country_map_by_score.html"
OUTPUT_HTML_TRIALS = REPORTS_DIR / "development_country_map_by_trial_count.html"
OUTPUT_HTML_ACTIVE = REPORTS_DIR / "development_country_map_by_active_trials.html"


def main():
    print("Reading country summary...")

    df = pd.read_excel(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")
    print(f"Countries before filtering: {df['country'].nunique()}")

    # Remove non-geographic placeholder
    df = df[df["country"] != "Country not reported"].copy()

    print(f"Countries after filtering: {df['country'].nunique()}")

    # -----------------------------
    # Map 1: Development activity score
    # -----------------------------
    fig_score = px.choropleth(
        df,
        locations="country",
        locationmode="country names",
        color="country_development_score",
        hover_name="country",
        hover_data={
            "trial_count": True,
            "active_trial_count": True,
            "product_family_count": True,
            "therapeutic_area_count": True,
            "sponsor_count": True,
            "median_enrollment": True,
            "country_development_score": True,
        },
        title="LAI Phase 1–3 Development Activity Score by Country",
    )

    fig_score.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    fig_score.write_html(OUTPUT_HTML_SCORE)

    print(f"Saved map: {OUTPUT_HTML_SCORE}")

    # -----------------------------
    # Map 2: Trial count
    # -----------------------------
    fig_trials = px.choropleth(
        df,
        locations="country",
        locationmode="country names",
        color="trial_count",
        hover_name="country",
        hover_data={
            "trial_count": True,
            "active_trial_count": True,
            "product_family_count": True,
            "therapeutic_area_count": True,
            "sponsor_count": True,
            "median_enrollment": True,
            "country_development_score": True,
        },
        title="LAI Phase 1–3 Development Trial Count by Country",
    )

    fig_trials.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    fig_trials.write_html(OUTPUT_HTML_TRIALS)

    print(f"Saved map: {OUTPUT_HTML_TRIALS}")

    # -----------------------------
    # Map 3: Active trial count
    # -----------------------------
    fig_active = px.choropleth(
        df,
        locations="country",
        locationmode="country names",
        color="active_trial_count",
        hover_name="country",
        hover_data={
            "trial_count": True,
            "active_trial_count": True,
            "product_family_count": True,
            "therapeutic_area_count": True,
            "sponsor_count": True,
            "median_enrollment": True,
            "country_development_score": True,
        },
        title="Active LAI Phase 1–3 Development Trials by Country",
    )

    fig_active.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    fig_active.write_html(OUTPUT_HTML_ACTIVE)

    print(f"Saved map: {OUTPUT_HTML_ACTIVE}")

    print("\n======================================")
    print("Interactive country maps created.")
    print("Open these files in your browser:")
    print(OUTPUT_HTML_SCORE)
    print(OUTPUT_HTML_TRIALS)
    print(OUTPUT_HTML_ACTIVE)


if __name__ == "__main__":
    main()