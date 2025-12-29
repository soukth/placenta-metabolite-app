import requests
import pandas as pd
import time
import re

EUROPE_PMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

PLACENTA_KEYWORDS = [
    "placenta", "pregnancy", "trophoblast", "decidua", "gestation"
]

PATHWAY_MAP = {
    "arginine": ("Amino Acid Metabolism", "Urea cycle / Nitric oxide synthesis"),
    "tryptophan": ("Amino Acid Metabolism", "Kynurenine pathway"),
    "glutamine": ("Amino Acid Metabolism", "Nitrogen metabolism"),
    "glutamic": ("Amino Acid Metabolism", "Neurotransmitter precursor"),
    "lysine": ("Amino Acid Metabolism", "Protein biosynthesis"),
    "phenylalanine": ("Amino Acid Metabolism", "Tyrosine biosynthesis"),
    "tyrosine": ("Amino Acid Metabolism", "Catecholamine synthesis"),
    "lipid": ("Lipid Metabolism", "Fatty acid metabolism"),
    "estriol": ("Hormone Biosynthesis", "Steroid hormone metabolism"),
    "estrane": ("Hormone Biosynthesis", "Steroid biosynthesis"),
}

DEFAULT_PATHWAYS = [
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

def europe_pmc_search(term):
    clean = term.lower().replace("dl-", "").replace("-", " ")
    query = f'({clean} OR "{clean}")'
    params = {
        "query": query,
        "format": "json",
        "pageSize": 10
    }
    try:
        r = requests.get(EUROPE_PMC_API, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("resultList", {}).get("result", [])
    except Exception:
        return []
def has_placenta_context(result):
    text = f"{result.get('title','')} {result.get('abstractText','')}".lower()
    for k in ["placenta", "pregnancy", "trophoblast", "decidua", "gestation"]:
        if k in text:
            return True
    return False

def classify_evidence(term, results):
    clean = term.lower().replace("dl-", "").replace("-", " ")
    for r in results:
        text = f"{r.get('title','')} {r.get('abstractText','')}".lower()
        if clean in text and has_placenta_context(r):
            return "Direct"
    for r in results:
        if has_placenta_context(r):
            return "Indirect"
    return "None"


def infer_pathway(term):
    t = term.lower()
    for key in PATHWAY_MAP:
        if key in t:
            return PATHWAY_MAP[key]
    return ("Not available", "Not available")

def pathway_placenta_evidence(pathway, results):
    if pathway == "Not available":
        return "Not available"
    for r in results:
        text = f"{r.get('title','')} {r.get('abstractText','')}".lower()
        if pathway.lower().split()[0] in text:
            return "Pathway reported in placenta"
    return "Unknown"

def analyze_all(df):
    rows = []

    for item in df.iloc[:, 0].astype(str):
        time.sleep(0.3)  # polite rate limiting

        results = europe_pmc_search(item)
        evidence = classify_evidence(item, results)

        doi = "Not found"
        title = "Not found"
        journal = "Not found"
        year = "Not found"

        if results:
            r0 = results[0]
            doi = r0.get("doi", "Not found")
            title = r0.get("title", "Not found")
            journal = r0.get("journalTitle", "Not found")
            year = r0.get("pubYear", "Not found")

        pathway, process = infer_pathway(item)
        pathway_evidence = pathway_placenta_evidence(pathway, results)

        rows.append({
            "Metabolite": item,
            "Metabolic_Process": process,
            "PubMed_DOI": doi,
            "Paper_Title": title,
            "Journal": journal,
            "Year": year,
            "Evidence_Type": evidence,
            "Pathway": pathway,
            "Pathway_Placenta_Evidence": pathway_evidence,
            "Google_Scholar_Link": f"https://scholar.google.com/scholar?q={item}+placenta+pregnancy"
        })

    return pd.DataFrame(rows)

def run_analysis(input_excel, output_excel):
    df = pd.read_excel(input_excel)
    result_df = analyze_all(df)
    result_df.to_excel(output_excel, index=False)
    return output_excel

