import os
import fitz  # PyMuPDF
import pandas as pd
import requests


# -------------------------------
# TEXT EXTRACTION
# -------------------------------
def extract_text_from_pdf(pdf_path):

    text = ""

    try:
        doc = fitz.open(pdf_path)

        for page in doc:
            text += page.get_text()

    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return text.lower()


# -------------------------------
# PUBMED SEARCH
# -------------------------------
def fetch_pubmed_links(term):

    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

        params = {
            "db": "pubmed",
            "term": f"{term} placenta human",
            "retmode": "json",
            "retmax": 2
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        ids = data["esearchresult"]["idlist"]

        links = [
            f"https://pubmed.ncbi.nlm.nih.gov/{pid}"
            for pid in ids
        ]

        return ", ".join(links) if links else "Not found"

    except:
        return "Not found"


# -------------------------------
# ORGAN + SPECIES DETECTION
# -------------------------------
ORGANS = [
    "placenta",
    "decidua",
    "trophoblast",
    "chorion"
]

SPECIES = [
    "human",
    "mouse",
    "rat",
    "macaque",
    "primate"
]


def detect_organ_species(text):

    organ_found = "Not found"
    species_found = "Not found"

    for organ in ORGANS:
        if organ in text:
            organ_found = organ
            break

    for sp in SPECIES:
        if sp in text:
            species_found = sp
            break

    return organ_found, species_found


# -------------------------------
# SINGLE PDF ANALYSIS
# -------------------------------
def analyze_pdf(pdf_path):

    text = extract_text_from_pdf(pdf_path)

    entity_name = os.path.basename(pdf_path).replace(".pdf", "")

    pubmed_links = fetch_pubmed_links(entity_name)

    organ, species = detect_organ_species(text)

    return {
        "Entity": entity_name,
        "PubMed_Evidence": pubmed_links,
        "Organ": organ,
        "Species": species
    }


# -------------------------------
# MAIN PIPELINE (REQUIRED)
# -------------------------------
def analyze_all(upload_folder, output_file="analysis_results.xlsx"):

    results = []

    pdf_files = [
        f for f in os.listdir(upload_folder)
        if f.endswith(".pdf")
    ]

    total = len(pdf_files)
    print(f"Processing {total} PDFs")

    for i, pdf in enumerate(pdf_files, 1):

        file_path = os.path.join(upload_folder, pdf)

        print(f"Analyzing {i}/{total}: {pdf}")

        res = analyze_pdf(file_path)

        results.append(res)

    df = pd.DataFrame(results)

    df.to_excel(output_file, index=False)

    print("Analysis complete")

    return output_file
