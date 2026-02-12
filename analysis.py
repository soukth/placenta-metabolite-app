# ==============================
# Placenta Literature Analyzer
# Deploy‑Safe Full Analysis Code
# ==============================

import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# PDF + OCR
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import cv2
from pdf2image import convert_from_path

# ==============================
# CONFIG
# ==============================

MAX_THREADS = 6
OUTPUT_FILE = "analysis_results.xlsx"

PLACENTA_KEYWORDS = [
    "placenta",
    "placental",
    "trophoblast",
    "chorionic",
    "fetal maternal interface"
]

PATHWAY_GROUPS = [
    "Immune Response Regulation",
    "Cell Cycle Control",
    "Apoptosis Signaling",
    "Transcriptional Regulation",
    "DNA Repair Mechanisms",
    "Protein Folding and Stability",
    "Cellular Stress Response",
    "Neurotransmitter Signaling",
    "Lipid Metabolism",
    "Extracellular Matrix Organization"
]

# ==============================
# UTILITIES
# ==============================

def contains_placenta_context(text):
    text = text.lower()
    return any(k in text for k in PLACENTA_KEYWORDS)


# ==============================
# PUBMED SEARCH
# ==============================

def search_pubmed(entity):
    try:
        url = f"https://pubmed.ncbi.nlm.nih.gov/?term={entity}+placenta+human"
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        article = soup.find("a", class_="docsum-title")
        if not article:
            return "Not found", "Not found"

        link = "https://pubmed.ncbi.nlm.nih.gov" + article.get("href")

        # Open article page
        r2 = requests.get(link, timeout=15)
        soup2 = BeautifulSoup(r2.text, "html.parser")

        doi_tag = soup2.find("span", class_="citation-doi")
        doi = doi_tag.text.replace("doi: ", "") if doi_tag else "Not found"

        return doi, link

    except Exception:
        return "Not found", "Not found"


# ==============================
# EUROPE PMC SEARCH
# ==============================

def search_europe_pmc(entity):
    try:
        url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            f"?query={entity}+placenta+human&format=json&pageSize=1"
        )

        r = requests.get(url, timeout=15)
        data = r.json()

        if "resultList" not in data or not data["resultList"]["result"]:
            return "Not found"

        doi = data["resultList"]["result"][0].get("doi", "Not found")
        return doi

    except Exception:
        return "Not found"


# ==============================
# GOOGLE SCHOLAR LINK
# ==============================

def scholar_link(entity):
    query = entity.replace(" ", "+")
    return f"https://scholar.google.com/scholar?q={query}+placenta+human"


# ==============================
# PATHWAY INFERENCE (Keyword Logic)
# ==============================

def infer_pathway(entity):
    e = entity.lower()

    if any(x in e for x in ["lipid", "fatty", "cholesterol"]):
        return "Lipid Metabolism"

    if any(x in e for x in ["neuro", "dopamine", "serotonin"]):
        return "Neurotransmitter Signaling"

    if any(x in e for x in ["collagen", "matrix", "integrin"]):
        return "Extracellular Matrix Organization"

    if any(x in e for x in ["dna", "repair", "p53"]):
        return "DNA Repair Mechanisms"

    if any(x in e for x in ["apoptosis", "caspase"]):
        return "Apoptosis Signaling"

    if any(x in e for x in ["immune", "interleukin", "tnf"]):
        return "Immune Response Regulation"

    return "Not available"


# ==============================
# PDF OCR EXTRACTION
# ==============================

def extract_text_from_pdf(pdf_path):
    text_content = ""

    try:
        doc = fitz.open(pdf_path)

        for page in doc:
            text_content += page.get_text()

        # Convert pages to images for OCR
        images = convert_from_path(pdf_path)

        for img in images:
            img_np = cv2.cvtColor(
                cv2.imread(img.filename), cv2.COLOR_BGR2GRAY
            )
            text_content += pytesseract.image_to_string(img_np)

    except Exception:
        pass

    return text_content


# ==============================
# CORE ANALYSIS
# ==============================

def analyze_entity(entity):
    pubmed_doi, pubmed_link = search_pubmed(entity)
    europe_doi = search_europe_pmc(entity)
    pathway = infer_pathway(entity)
    scholar = scholar_link(entity)

    return {
        "Entity": entity,
        "PubMed_DOI": pubmed_doi,
        "EuropePMC_DOI": europe_doi,
        "Scholar_Link": scholar,
        "Pathway": pathway,
    }


# ==============================
# PARALLEL ANALYSIS
# ==============================

def analyze_all(entities):
    results = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(analyze_entity, e): e for e in entities}

        for future in as_completed(futures):
            results.append(future.result())
            print(f"Processed: {futures[future]}")

    return results


# ==============================
# EXCEL EXPORT
# ==============================

def save_results(results):
    df = pd.DataFrame(results)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved → {OUTPUT_FILE}")


# ==============================
# MAIN EXECUTION
# ==============================

def run_analysis(excel_file, column_name="Gene"):
    df = pd.read_excel(excel_file)

    if column_name not in df.columns:
        raise Exception(f"Column '{column_name}' not found")

    entities = df[column_name].dropna().tolist()

    print(f"Analyzing {len(entities)} entities…\n")

    results = analyze_all(entities)
    save_results(results)


# ==============================
# CLI ENTRY
# ==============================

if __name__ == "__main__":
    # Example usage
    run_analysis("input.xlsx", column_name="Gene")
