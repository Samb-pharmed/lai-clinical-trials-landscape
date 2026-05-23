import time
import requests
import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

REFERENCE_FILE = PROJECT_ROOT / "data" / "reference" / "lai_product_dictionary_v1.xlsx"

RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = RAW_DIR / "lai_clinical_trials_raw.csv"
OUTPUT_XLSX = RAW_DIR / "lai_clinical_trials_raw.xlsx"


# -----------------------------
# API settings
# -----------------------------
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

PAGE_SIZE = 100
SLEEP_SECONDS = 0.2


# -----------------------------
# Helper functions
# -----------------------------
def safe_get(dictionary, keys, default=None):
    """
    Safely extract a nested value from a dictionary.

    Example:
    safe_get(study, ["protocolSection", "identificationModule", "nctId"])
    """
    current_value = dictionary

    for key in keys:
        if not isinstance(current_value, dict):
            return default

        current_value = current_value.get(key)

        if current_value is None:
            return default

    return current_value


def list_to_text(value, separator=" | "):
    """
    Convert lists, dictionaries, or strings into readable text for Excel/CSV.
    """
    if value is None:
        return ""

    if isinstance(value, list):
        cleaned_items = []

        for item in value:
            if isinstance(item, dict):
                cleaned_items.append(str(item))
            else:
                cleaned_items.append(str(item))

        return separator.join(cleaned_items)

    if isinstance(value, dict):
        return str(value)

    return str(value)


def extract_interventions(study):
    interventions = safe_get(
        study,
        ["protocolSection", "armsInterventionsModule", "interventions"],
        default=[]
    )

    names = []
    types = []
    descriptions = []

    for intervention in interventions:
        names.append(intervention.get("name", ""))
        types.append(intervention.get("type", ""))
        descriptions.append(intervention.get("description", ""))

    return {
        "intervention_names": list_to_text(names),
        "intervention_types": list_to_text(types),
        "intervention_descriptions": list_to_text(descriptions),
    }


def extract_arm_groups(study):
    arm_groups = safe_get(
        study,
        ["protocolSection", "armsInterventionsModule", "armGroups"],
        default=[]
    )

    labels = []
    types = []
    descriptions = []

    for arm in arm_groups:
        labels.append(arm.get("label", ""))
        types.append(arm.get("type", ""))
        descriptions.append(arm.get("description", ""))

    return {
        "arm_group_labels": list_to_text(labels),
        "arm_group_types": list_to_text(types),
        "arm_group_descriptions": list_to_text(descriptions),
    }


def extract_collaborators(study):
    collaborators = safe_get(
        study,
        ["protocolSection", "sponsorCollaboratorsModule", "collaborators"],
        default=[]
    )

    collaborator_names = []

    for collaborator in collaborators:
        collaborator_names.append(collaborator.get("name", ""))

    return list_to_text(collaborator_names)


def extract_locations(study):
    locations = safe_get(
        study,
        ["protocolSection", "contactsLocationsModule", "locations"],
        default=[]
    )

    facilities = []
    cities = []
    states = []
    countries = []

    for location in locations:
        facilities.append(location.get("facility", ""))
        cities.append(location.get("city", ""))
        states.append(location.get("state", ""))
        countries.append(location.get("country", ""))

    unique_countries = sorted(set([country for country in countries if country]))

    return {
        "location_facilities": list_to_text(facilities),
        "location_cities": list_to_text(cities),
        "location_states": list_to_text(states),
        "location_countries": list_to_text(countries),
        "number_of_sites": len(locations),
        "number_of_countries": len(unique_countries),
        "unique_countries": list_to_text(unique_countries),
    }


def extract_outcomes(study):
    primary_outcomes = safe_get(
        study,
        ["protocolSection", "outcomesModule", "primaryOutcomes"],
        default=[]
    )

    secondary_outcomes = safe_get(
        study,
        ["protocolSection", "outcomesModule", "secondaryOutcomes"],
        default=[]
    )

    primary_measures = []
    secondary_measures = []

    for outcome in primary_outcomes:
        measure = outcome.get("measure", "")
        timeframe = outcome.get("timeFrame", "")
        primary_measures.append(f"{measure} [{timeframe}]")

    for outcome in secondary_outcomes:
        measure = outcome.get("measure", "")
        timeframe = outcome.get("timeFrame", "")
        secondary_measures.append(f"{measure} [{timeframe}]")

    return {
        "primary_outcomes": list_to_text(primary_measures),
        "secondary_outcomes": list_to_text(secondary_measures),
    }


def extract_study_fields(study):
    """
    Extract the study-level fields needed for the LAI clinical trials project.
    """
    protocol = study.get("protocolSection", {})

    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    design_info = design.get("designInfo", {})
    conditions = protocol.get("conditionsModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    description = protocol.get("descriptionModule", {})
    eligibility = protocol.get("eligibilityModule", {})

    enrollment_info = design.get("enrollmentInfo", {})
    lead_sponsor = sponsor.get("leadSponsor", {})

    intervention_fields = extract_interventions(study)
    arm_group_fields = extract_arm_groups(study)
    location_fields = extract_locations(study)
    outcome_fields = extract_outcomes(study)

    row = {
        # Identification
        "nct_id": identification.get("nctId", ""),
        "brief_title": identification.get("briefTitle", ""),
        "official_title": identification.get("officialTitle", ""),
        "acronym": identification.get("acronym", ""),

        # Status and dates
        "overall_status": status.get("overallStatus", ""),
        "start_date": safe_get(status, ["startDateStruct", "date"], ""),
        "start_date_type": safe_get(status, ["startDateStruct", "type"], ""),
        "primary_completion_date": safe_get(status, ["primaryCompletionDateStruct", "date"], ""),
        "primary_completion_date_type": safe_get(status, ["primaryCompletionDateStruct", "type"], ""),
        "completion_date": safe_get(status, ["completionDateStruct", "date"], ""),
        "completion_date_type": safe_get(status, ["completionDateStruct", "type"], ""),
        "study_first_submit_date": status.get("studyFirstSubmitDate", ""),
        "last_update_submit_date": status.get("lastUpdateSubmitDate", ""),

        # Study design
        "study_type": design.get("studyType", ""),
        "phases": list_to_text(design.get("phases", [])),
        "enrollment_count": enrollment_info.get("count", ""),
        "enrollment_type": enrollment_info.get("type", ""),
        "allocation": design_info.get("allocation", ""),
        "intervention_model": design_info.get("interventionModel", ""),
        "masking": safe_get(design_info, ["maskingInfo", "masking"], ""),
        "primary_purpose": design_info.get("primaryPurpose", ""),

        # Conditions
        "conditions": list_to_text(conditions.get("conditions", [])),
        "keywords": list_to_text(conditions.get("keywords", [])),

        # Sponsor
        "lead_sponsor_name": lead_sponsor.get("name", ""),
        "lead_sponsor_class": lead_sponsor.get("class", ""),
        "collaborators": extract_collaborators(study),

        # Text fields
        "brief_summary": description.get("briefSummary", ""),
        "detailed_description": description.get("detailedDescription", ""),
        "eligibility_criteria": eligibility.get("eligibilityCriteria", ""),
        "sex": eligibility.get("sex", ""),
        "minimum_age": eligibility.get("minimumAge", ""),
        "maximum_age": eligibility.get("maximumAge", ""),
    }

    row.update(intervention_fields)
    row.update(arm_group_fields)
    row.update(location_fields)
    row.update(outcome_fields)

    return row


def search_clinical_trials(search_term):
    """
    Search ClinicalTrials.gov API v2 for one search term.
    Returns a list of study records.
    """
    all_studies = []
    page_token = None

    while True:
        params = {
            "query.term": search_term,
            "pageSize": PAGE_SIZE,
            "format": "json",
        }

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(BASE_URL, params=params, timeout=30)

        if response.status_code != 200:
            print(f"API error for term: {search_term}")
            print(f"Status code: {response.status_code}")
            print(response.text[:500])
            break

        data = response.json()

        studies = data.get("studies", [])
        all_studies.extend(studies)

        page_token = data.get("nextPageToken")

        if not page_token:
            break

        time.sleep(SLEEP_SECONDS)

    return all_studies


def main():
    print("Reading LAI product dictionary...")

    dictionary_df = pd.read_excel(REFERENCE_FILE)

    print(f"Products/formulations selected for search: {len(dictionary_df)}")

    all_rows = []

    for _, product in dictionary_df.iterrows():
        product_id = product["product_id"]
        brand_name = product["brand_name"]
        api_name = product["api_name"]
        category = product["category"]
        search_terms = str(product["search_terms"]).split(";")

        print("\n--------------------------------------")
        print(f"Searching product: {product_id} | {brand_name}")

        for raw_term in search_terms:
            search_term = raw_term.strip()

            if not search_term:
                continue

            print(f"  Search term: {search_term}")

            studies = search_clinical_trials(search_term)

            print(f"    Studies found: {len(studies)}")

            for study in studies:
                row = extract_study_fields(study)

                # Add matching metadata from our LAI dictionary
                row["matched_product_id"] = product_id
                row["matched_brand_name"] = brand_name
                row["matched_api_name"] = api_name
                row["matched_category"] = category
                row["matched_search_term"] = search_term
                row["search_source"] = "LAI dictionary"

                all_rows.append(row)

            time.sleep(SLEEP_SECONDS)

    if not all_rows:
        print("No studies found. Nothing to save.")
        return

    raw_df = pd.DataFrame(all_rows)

    # Put matching metadata columns first
    first_columns = [
        "matched_product_id",
        "matched_brand_name",
        "matched_api_name",
        "matched_category",
        "matched_search_term",
        "search_source",
    ]

    remaining_columns = [col for col in raw_df.columns if col not in first_columns]
    raw_df = raw_df[first_columns + remaining_columns]

    # Save full raw search results before deduplication
    raw_df.to_csv(OUTPUT_CSV, index=False)
    raw_df.to_excel(OUTPUT_XLSX, index=False)

    print("\n======================================")
    print("Download complete.")
    print(f"Raw rows saved: {len(raw_df)}")
    print(f"Unique NCT IDs: {raw_df['nct_id'].nunique()}")
    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved Excel: {OUTPUT_XLSX}")

    print("\nTop matched categories:")
    print(raw_df["matched_category"].value_counts())

    print("\nTop search terms:")
    print(raw_df["matched_search_term"].value_counts().head(20))


if __name__ == "__main__":
    main()