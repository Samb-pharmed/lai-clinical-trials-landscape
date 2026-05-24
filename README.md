# Long-Acting Injectable (LAI) Clinical Trials Landscape

A data science project analysing the clinical-trial landscape of long-acting injectables (LAIs), depot formulations, implants, and extended-release injectable products using ClinicalTrials.gov API data.

The project builds a curated LAI product dictionary, downloads clinical-trial records, cleans and deduplicates the dataset, performs relevance scoring, generates exploratory data analysis (EDA), and creates development-focused benchmarks by therapeutic area, product family, sponsor, phase, enrolment, duration, and geography.

## Author

**Saeid Bazraei**  
GitHub: [Samb-pharmed](https://github.com/Samb-pharmed)

## Project Objectives

The main objectives of this project are to:

- Build a structured dictionary of marketed and pipeline LAI/depot/extended-release injectable products.
- Retrieve clinical-trial records from ClinicalTrials.gov using product-specific search terms.
- Clean, deduplicate, and relevance-score trial records.
- Create broad, strict, and development-focused analytical datasets.
- Analyse LAI clinical development patterns by phase, therapeutic area, product family, sponsor, geography, trial duration, and enrolment.
- Generate visual outputs and benchmark tables suitable for portfolio, R&D strategy, and data science demonstration.

## Why This Project Matters

Long-acting injectable products are important across several therapeutic areas, including psychiatry, addiction medicine, hormonal oncology, endocrine peptide therapy, pain management, contraception, HIV treatment/prevention, and supportive care.

This project demonstrates how public clinical-trial data can be transformed into a structured strategic dataset for understanding:

- Which LAI product families have the largest evidence base.
- Which therapeutic areas dominate LAI clinical development.
- Typical enrolment and trial-duration benchmarks.
- Which countries are most active in LAI Phase 1-3 development.
- Which sponsors and product families are most active in current LAI development.

## Data Source

The clinical-trial data are retrieved from:

- [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api)

The original data belong to ClinicalTrials.gov. This repository contains code and derived analysis outputs. Users should follow ClinicalTrials.gov terms of use and attribution expectations when reusing the data.

## Project Workflow

The project follows a reproducible step-by-step workflow:

| Step | Script | Purpose |
|---:|---|---|
| 1 | `01_create_lai_dictionary.py` | Create the curated LAI product dictionary |
| 2 | `02_download_clinical_trials.py` | Download raw ClinicalTrials.gov records using dictionary search terms |
| 3 | `03_deduplicate_trials.py` | Deduplicate records by NCT ID while preserving match history |
| 4 | `04_relevance_filter_trials.py` | Score and classify trial relevance |
| 5 | `05_create_analysis_dataset.py` | Create the initial cleaned broad analysis dataset |
| 6 | `06_visual_eda.py` | Generate first EDA plots and tables |
| 7 | `07_create_enhanced_datasets.py` | Create broad and strict enhanced datasets with sponsor and product-family classification |
| 8 | `08_strict_enhanced_eda.py` | Generate strict dataset EDA |
| 9 | `09_qc_outliers_and_active_trials.py` | Create QC workbook for outliers, active trials, and development subsets |
| 10 | `10_create_development_subset.py` | Create Phase 1-3 interventional development subset |
| 11 | `11_development_subset_eda.py` | Generate development-focused EDA |
| 12 | `12_development_geography_analysis.py` | Analyse country-level development activity |
| 13 | `13_create_interactive_country_map.py` | Create interactive Plotly country maps |
| 14 | `14_country_strategy_summary.py` | Create country-level strategic summary workbook |
| 15 | `15_product_benchmarks.py` | Create product-family benchmark workbook |

## Repository Structure

```text
lai-clinical-trials-landscape/
|
├── data/
│   ├── reference/        # Curated LAI product dictionary
│   ├── raw/              # Raw downloaded ClinicalTrials.gov records
│   └── processed/        # Cleaned and analysis-ready datasets
|
├── reports/
│   ├── figures/          # Static EDA figures
│   ├── tables/           # Excel summary tables and QC workbooks
│   └── *.html            # Interactive Plotly maps
|
├── scripts/              # Stepwise project scripts
|
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Main Analytical Datasets

The workflow creates several datasets with different analytical uses:

| Dataset | Purpose |
|---|---|
| `lai_clinical_trials_raw.xlsx` | Full raw API search output, including duplicate NCT IDs |
| `lai_clinical_trials_deduplicated.xlsx` | One row per NCT ID with all matched terms preserved |
| `lai_clinical_trials_relevance_scored.xlsx` | Deduplicated dataset with relevance scores and flags |
| `lai_clinical_trials_broad_enhanced.xlsx` | Broad candidate LAI dataset: High + Medium + Review |
| `lai_clinical_trials_strict_enhanced.xlsx` | High-confidence LAI dataset |
| `lai_clinical_trials_development_subset.xlsx` | Strict, interventional Phase 1-3 development subset |

## Key Outputs

The project produces:

- Static EDA charts in `reports/figures/`
- Excel summary tables in `reports/tables/`
- Interactive country maps in `reports/`
- Product-family benchmark workbooks
- Country-level development and recruitment intelligence tables

Example output categories include:

- Trials by therapeutic area
- Trials by product family
- Trials by clinical phase
- Trials by study status
- Trial start-year trends
- Median enrolment by phase
- Median enrolment by product family
- Median trial duration by product family
- Top sponsors
- Top countries by development activity
- Active trial hotspots
- Product-family geography matrices

## Example Insights Generated

The analysis can identify patterns such as:

- Addiction, psychiatry/CNS, and GnRH/hormonal oncology are major LAI development areas.
- Phase 4 and post-marketing studies dominate the full LAI evidence landscape, while Phase 1-3 interventional trials are more suitable for development benchmarking.
- Median enrolment is more informative than mean enrolment due to large outlier trials.
- The United States dominates ClinicalTrials.gov-registered LAI development activity.
- Canada, Germany, China, France, Spain, the United Kingdom, Italy, and Belgium are important secondary geographies for LAI Phase 1-3 development.
- Product-family level analysis is more actionable than therapeutic-area analysis alone.

## Interactive Maps

The interactive Plotly maps are hosted through GitHub Pages:

- [Development activity score map](https://samb-pharmed.github.io/lai-clinical-trials-landscape/reports/maps/development_country_map_by_score.html)
- [Trial count map](https://samb-pharmed.github.io/lai-clinical-trials-landscape/reports/maps/development_country_map_by_trial_count.html)
- [Active trials map](https://samb-pharmed.github.io/lai-clinical-trials-landscape/reports/maps/development_country_map_by_active_trials.html)

If the GitHub file preview does not render, use the GitHub Pages links above or download the HTML file and open it locally.

## Installation

Clone the repository:

```bash
git clone https://github.com/Samb-pharmed/lai-clinical-trials-landscape.git
cd lai-clinical-trials-landscape
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

Run the scripts in numerical order:

```bash
python scripts/01_create_lai_dictionary.py
python scripts/02_download_clinical_trials.py
python scripts/03_deduplicate_trials.py
python scripts/04_relevance_filter_trials.py
python scripts/05_create_analysis_dataset.py
python scripts/06_visual_eda.py
python scripts/07_create_enhanced_datasets.py
python scripts/08_strict_enhanced_eda.py
python scripts/09_qc_outliers_and_active_trials.py
python scripts/10_create_development_subset.py
python scripts/11_development_subset_eda.py
python scripts/12_development_geography_analysis.py
python scripts/13_create_interactive_country_map.py
python scripts/14_country_strategy_summary.py
python scripts/15_product_benchmarks.py
```

## Methodological Notes

This project uses a dictionary-driven search approach. Each LAI product is represented by brand names, API names, and search terms. ClinicalTrials.gov records are retrieved using those terms, then deduplicated by NCT ID.

Relevance scoring gives higher confidence to records where product terms appear in intervention fields, arm descriptions, or study titles. Matches found only in summaries or condition fields are treated as weaker evidence.

Three dataset levels are created:

1. **Broad dataset**: inclusive landscape exploration.
2. **Strict dataset**: high-confidence LAI trial landscape.
3. **Development subset**: strict, interventional Phase 1-3 trials for development benchmarking.

## Limitations

This project has important limitations:

- ClinicalTrials.gov is not a complete global clinical-trial registry.
- The dataset is influenced by US registration practices.
- Search-term based retrieval can produce false positives and false negatives.
- Relevance scoring is rule-based and should be manually validated for final regulatory or commercial use.
- Product-family classification is rule-based and may require refinement.
- Country counts are based on reported trial locations in ClinicalTrials.gov.
- Multi-country trials are counted once per participating country in geography analyses.

## Recommended Future Improvements

Possible extensions include:

- Manual validation of the strict dataset.
- Addition of other registries such as EU Clinical Trials Register, ISRCTN, and WHO ICTRP.
- Improved NLP-based intervention role detection.
- Sponsor normalisation using a controlled sponsor dictionary.
- Interactive dashboard using Streamlit, Dash, or Plotly.
- Machine-learning model to predict enrolment size or trial duration.
- Product-specific benchmark reports for selected LAI families.

## Skills Demonstrated

This project demonstrates:

- API data extraction
- Clinical-trial data engineering
- Data cleaning and deduplication
- Rule-based NLP and relevance scoring
- Exploratory data analysis
- Pharma R&D landscape analysis
- Product-family classification
- Geographic analysis
- Interactive visualisation
- Reproducible project structure
- Python, pandas, matplotlib, Plotly, and Excel reporting

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Disclaimer

This project is for educational, portfolio, and research demonstration purposes. It is not intended as regulatory, clinical, medical, investment, or commercial advice. Results should be independently validated before use in formal decision-making.
