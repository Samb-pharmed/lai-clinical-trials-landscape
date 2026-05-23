# Data

This project uses ClinicalTrials.gov API v2 as the source of clinical-trial records.

## Included data

The repository includes the curated LAI product dictionary in:

- `data/reference/lai_product_dictionary_v1.xlsx`
- `data/reference/lai_product_dictionary_v1.csv`

This dictionary is used to search ClinicalTrials.gov.

## Not included data

The following folders are not included in the repository because they are generated outputs and may be large:

- `data/raw/`
- `data/processed/`
- `reports/tables/`

To recreate the data, run the scripts in numerical order from the project root.