import pandas as pd
from pathlib import Path


# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "lai_clinical_trials_relevance_scored.xlsx"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

BROAD_OUTPUT_CSV = PROCESSED_DIR / "lai_clinical_trials_broad_enhanced.csv"
BROAD_OUTPUT_XLSX = PROCESSED_DIR / "lai_clinical_trials_broad_enhanced.xlsx"

STRICT_OUTPUT_CSV = PROCESSED_DIR / "lai_clinical_trials_strict_enhanced.csv"
STRICT_OUTPUT_XLSX = PROCESSED_DIR / "lai_clinical_trials_strict_enhanced.xlsx"


# -----------------------------
# Helper functions
# -----------------------------
def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).lower().strip()


def first_available_text(row, columns):
    """
    Join selected row fields into one lower-case searchable text block.
    """
    return " ".join([clean_text(row.get(col, "")) for col in columns])


def normalize_sponsor_name(sponsor_name):
    """
    Normalise sponsor names into cleaner company/institution groups.
    This is rule-based and should be refined as we inspect outputs.
    """
    text = clean_text(sponsor_name)

    if not text:
        return "Unknown"

    sponsor_rules = [
        ("johnson & johnson", "Johnson & Johnson / Janssen"),
        ("janssen", "Johnson & Johnson / Janssen"),
        ("otsuka", "Otsuka"),
        ("alkermes", "Alkermes"),
        ("indivior", "Indivior"),
        ("camurus", "Camurus"),
        ("debiopharm", "Debiopharm"),
        ("tolmar", "Tolmar"),
        ("pacira", "Pacira"),
        ("heron therapeutics", "Heron Therapeutics"),
        ("durect", "DURECT"),
        ("braeburn", "Braeburn"),
        ("astrazeneca", "AstraZeneca"),
        ("novartis", "Novartis"),
        ("ipsen", "Ipsen"),
        ("pfizer", "Pfizer"),
        ("eli lilly", "Eli Lilly"),
        ("lilly", "Eli Lilly"),
        ("takeda", "Takeda"),
        ("teva", "Teva"),
        ("lundbeck", "Lundbeck"),
        ("roche", "Roche"),
        ("abbvie", "AbbVie"),
        ("gilead", "Gilead"),
        ("viiv", "ViiV Healthcare"),
        ("glaxosmithkline", "GSK"),
        ("gsk", "GSK"),
        ("rhythm pharmaceuticals", "Rhythm Pharmaceuticals"),
        ("flexion", "Flexion Therapeutics"),
        ("national institute on drug abuse", "NIDA"),
        ("nida", "NIDA"),
        ("national cancer institute", "National Cancer Institute"),
        ("nci", "National Cancer Institute"),
        ("national institutes of health", "NIH"),
        ("nih", "NIH"),
        ("yale", "Yale University"),
        ("johns hopkins", "Johns Hopkins University"),
        ("university of pennsylvania", "University of Pennsylvania"),
        ("university of california", "University of California"),
        ("mayo clinic", "Mayo Clinic"),
        ("massachusetts general hospital", "Massachusetts General Hospital"),
        ("cairo university", "Cairo University"),
    ]

    for pattern, normalized_name in sponsor_rules:
        if pattern in text:
            return normalized_name

    return sponsor_name


def classify_product_family(row):
    """
    Product family classification based on matched terms, API names,
    intervention names, titles, and categories.
    """
    text = first_available_text(
        row,
        [
            "matched_brand_names",
            "matched_api_names",
            "matched_search_terms",
            "intervention_names",
            "intervention_descriptions",
            "arm_group_labels",
            "arm_group_descriptions",
            "brief_title",
            "official_title",
            "matched_categories",
        ]
    )

    # Antipsychotic LAIs
    if any(term in text for term in ["paliperidone", "invega", "xeplion", "trevicta", "byannli", "hafyera", "trinza", "pp1m", "pp3m", "pp6m", "palmeux"]):
        return "Paliperidone LAI"

    if any(term in text for term in ["risperdal", "risperidone", "perseris", "uzedy", "rykindo", "okedi"]):
        return "Risperidone LAI"

    if any(term in text for term in ["abilify", "aripiprazole", "aristada"]):
        return "Aripiprazole LAI"

    if any(term in text for term in ["olanzapine", "zyprexa", "zypadhera"]):
        return "Olanzapine LAI"

    if "haloperidol" in text or "haldol" in text:
        return "Haloperidol decanoate"

    if "fluphenazine" in text:
        return "Fluphenazine decanoate"

    if "zuclopenthixol" in text:
        return "Zuclopenthixol decanoate"

    if "flupentixol" in text:
        return "Flupentixol decanoate"

    # Somatostatin analogue / peptide depots
    if any(term in text for term in ["octreotide", "sandostatin", "oczyesa", "cam2029", "debio 4126", "debio4126"]):
        return "Octreotide depot"

    if any(term in text for term in ["lanreotide", "somatuline"]):
        return "Lanreotide depot"

    if any(term in text for term in ["pasireotide", "signifor"]):
        return "Pasireotide depot"

    # GnRH / hormonal depots
    if any(term in text for term in ["leuprolide", "leuprorelin", "lupron", "eligard", "prostap", "lutrate", "cam2032", "tol2506"]):
        return "Leuprolide / leuprorelin depot"

    if any(term in text for term in ["goserelin", "zoladex"]):
        return "Goserelin implant"

    if any(term in text for term in ["triptorelin", "trelstar", "decapeptyl", "gonapeptyl", "debio 4326", "debio4326"]):
        return "Triptorelin depot"

    if any(term in text for term in ["histrelin", "vantas", "supprelin"]):
        return "Histrelin implant"

    if any(term in text for term in ["degarelix", "debio 4228", "debio4228", "tol3022"]):
        return "Degarelix depot / pipeline"

    # HIV LAIs
    if any(term in text for term in ["cabenuva", "cabotegravir", "rilpivirine"]):
        return "Cabotegravir / rilpivirine LAI"

    if any(term in text for term in ["apretude"]):
        return "Cabotegravir PrEP LAI"

    if any(term in text for term in ["lenacapavir", "sunlenca"]):
        return "Lenacapavir LAI"

    # Addiction LAIs
    if any(term in text for term in ["naltrexone", "vivitrol"]):
        return "Naltrexone ER"

    if any(term in text for term in ["buprenorphine", "sublocade", "brixadi", "buvidal", "cam2038", "indv-6001", "indv6001", "ala-1000"]):
        return "Buprenorphine depot"

    # Contraceptive depots
    if any(term in text for term in ["medroxyprogesterone", "depo-provera", "sayana", "dmpa"]):
        return "Medroxyprogesterone depot"

    if any(term in text for term in ["norethisterone", "norethindrone", "noristerat"]):
        return "Norethisterone enantate depot"

    # Metabolic
    if any(term in text for term in ["exenatide", "bydureon"]):
        return "Exenatide ER"

    # Local analgesic / anti-inflammatory / antiemetic
    if any(term in text for term in ["bupivacaine", "exparel", "zynrelef", "posimir", "liposomal bupivacaine"]):
        return "Bupivacaine ER / local depot"

    if any(term in text for term in ["triamcinolone", "zilretta"]):
        return "Triamcinolone ER"

    if any(term in text for term in ["granisetron", "sustol", "cam2047"]):
        return "Granisetron ER"

    # Other pipeline
    if any(term in text for term in ["setmelanotide", "cam4072"]):
        return "Setmelanotide depot"

    if any(term in text for term in ["treprostinil", "cam2043"]):
        return "Treprostinil depot"

    return "Other / unclassified"


def classify_therapeutic_area(row):
    """
    Reuse and slightly improve the therapeutic-area classification.
    """
    text = first_available_text(
        row,
        [
            "conditions",
            "brief_title",
            "official_title",
            "matched_categories",
            "intervention_names",
            "matched_api_names",
            "matched_brand_names",
            "product_family_clean",
        ]
    )

    if any(term in text for term in ["schizophrenia", "schizoaffective", "bipolar", "psychosis", "psychotic", "antipsychotic"]):
        return "Psychiatry / CNS"

    if any(term in text for term in ["opioid", "alcohol dependence", "substance use", "addiction", "withdrawal", "buprenorphine", "naltrexone"]):
        return "Addiction / substance use"

    if any(term in text for term in ["hiv", "human immunodeficiency virus", "pre-exposure prophylaxis", "prep", "cabotegravir", "rilpivirine", "lenacapavir"]):
        return "HIV / infectious disease"

    if any(term in text for term in ["acromegaly", "neuroendocrine", "carcinoid", "vipoma", "cushing", "somatostatin", "octreotide", "lanreotide", "pasireotide"]):
        return "Endocrinology / peptide depot"

    if any(term in text for term in ["prostate cancer", "breast cancer", "endometriosis", "fibroid", "precocious puberty", "central precocious puberty", "ovarian suppression", "leuprolide", "leuprorelin", "goserelin", "triptorelin", "histrelin", "degarelix"]):
        return "GnRH / hormonal oncology"

    if any(term in text for term in ["contraception", "contraceptive", "medroxyprogesterone", "norethisterone", "norethindrone", "dmpa"]):
        return "Contraception / women's health"

    if any(term in text for term in ["diabetes", "type 2 diabetes", "exenatide", "glucose", "glycemic"]):
        return "Metabolic / diabetes"

    if any(term in text for term in ["postoperative pain", "post-operative pain", "postsurgical", "post-surgical", "analgesia", "bupivacaine", "meloxicam", "surgical site"]):
        return "Pain / local analgesia"

    if any(term in text for term in ["osteoarthritis", "knee pain", "triamcinolone", "intra-articular", "zilretta"]):
        return "Local anti-inflammatory"

    if any(term in text for term in ["nausea", "vomiting", "chemotherapy-induced", "granisetron", "cinv"]):
        return "Supportive care / antiemetic"

    return "Other / unclassified"


def parse_date(value):
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


def add_analysis_columns(df):
    """
    Add cleaned analytical columns.
    """
    enhanced_df = df.copy()

    enhanced_df["sponsor_normalized"] = enhanced_df["lead_sponsor_name"].apply(
        normalize_sponsor_name
    )

    enhanced_df["product_family_clean"] = enhanced_df.apply(
        classify_product_family,
        axis=1
    )

    enhanced_df["therapeutic_area_clean"] = enhanced_df.apply(
        classify_therapeutic_area,
        axis=1
    )

    enhanced_df["enrollment_count_clean"] = pd.to_numeric(
        enhanced_df["enrollment_count"],
        errors="coerce"
    )

    enhanced_df["phase_clean"] = enhanced_df["phases"].apply(clean_phase)

    enhanced_df["start_date_parsed"] = enhanced_df["start_date"].apply(parse_date)
    enhanced_df["primary_completion_date_parsed"] = enhanced_df["primary_completion_date"].apply(parse_date)
    enhanced_df["completion_date_parsed"] = enhanced_df["completion_date"].apply(parse_date)

    enhanced_df["start_year"] = enhanced_df["start_date_parsed"].dt.year
    enhanced_df["primary_completion_year"] = enhanced_df["primary_completion_date_parsed"].dt.year
    enhanced_df["completion_year"] = enhanced_df["completion_date_parsed"].dt.year

    enhanced_df["duration_to_primary_completion_months"] = enhanced_df.apply(
        lambda row: calculate_duration_months(
            row["start_date_parsed"],
            row["primary_completion_date_parsed"]
        ),
        axis=1
    )

    enhanced_df["duration_to_study_completion_months"] = enhanced_df.apply(
        lambda row: calculate_duration_months(
            row["start_date_parsed"],
            row["completion_date_parsed"]
        ),
        axis=1
    )

    first_columns = [
        "nct_id",
        "relevance_flag",
        "relevance_score",
        "therapeutic_area_clean",
        "product_family_clean",
        "sponsor_normalized",
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

    remaining_columns = [col for col in enhanced_df.columns if col not in first_columns]
    enhanced_df = enhanced_df[first_columns + remaining_columns]

    return enhanced_df


def save_dataset(df, csv_path, xlsx_path):
    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)


def print_dataset_summary(df, dataset_name):
    print(f"\n======================================")
    print(f"{dataset_name} dataset summary")
    print(f"Rows: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    print("\nRelevance flags:")
    print(df["relevance_flag"].value_counts())

    print("\nTherapeutic areas:")
    print(df["therapeutic_area_clean"].value_counts())

    print("\nTop product families:")
    print(df["product_family_clean"].value_counts().head(20))

    print("\nTop normalized sponsors:")
    print(df["sponsor_normalized"].value_counts().head(20))


def main():
    print("Reading relevance-scored dataset...")
    df = pd.read_excel(INPUT_FILE)

    print(f"Input rows: {len(df)}")
    print(f"Unique NCT IDs: {df['nct_id'].nunique()}")

    # A. Broad dataset: inclusive analysis view
    broad_df = df[df["relevance_flag"].isin(["High", "Medium", "Review"])].copy()
    broad_df = add_analysis_columns(broad_df)

    # B. Strict dataset: high-confidence view
    strict_df = df[df["relevance_flag"] == "High"].copy()
    strict_df = add_analysis_columns(strict_df)

    save_dataset(broad_df, BROAD_OUTPUT_CSV, BROAD_OUTPUT_XLSX)
    save_dataset(strict_df, STRICT_OUTPUT_CSV, STRICT_OUTPUT_XLSX)

    print_dataset_summary(broad_df, "Broad")
    print_dataset_summary(strict_df, "Strict")

    print("\n======================================")
    print("Enhanced datasets created.")
    print(f"Broad CSV: {BROAD_OUTPUT_CSV}")
    print(f"Broad Excel: {BROAD_OUTPUT_XLSX}")
    print(f"Strict CSV: {STRICT_OUTPUT_CSV}")
    print(f"Strict Excel: {STRICT_OUTPUT_XLSX}")


if __name__ == "__main__":
    main()