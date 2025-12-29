import requests
import pandas as pd
from urllib.parse import quote

HEADERS = {"User-Agent": "Mozilla/5.0"}

PLACENTA_TERMS = [
    "placenta", "placental", "trophoblast", "chorionic",
    "pregnancy", "maternal", "fetal", "foetal"
]

ORGANS = {
    "Placenta": ["placenta", "placental"],
    "Decidua": ["decidua"],
    "Amniotic fluid": ["amniotic"],
    "Fetus": ["fetal", "foetal"],
    "Cord blood": ["cord blood", "umbilical"]
}

SPECIES = {
    "Human": ["human", "homo sapiens"],
    "Non-human primate": ["macaque", "rhesus", "primate"]
}

METABOLIC_PROCESSES = {
    "Amino Acid Metabolism": ["arginine", "glutamine", "lysine", "histidine", "phenylalanine", "tryptophan"],
    "Steroid Hormone Biosynthesis": ["estriol", "estradiol", "estrone"],
    "Lipid Metabolism": ["lipid", "fatty", "erucamide"],
    "Energy Metabolism": ["glucose", "lactate", "pyruvate"]
}


# ---------------------------
# Utility functions
# ---------------------------

def detect_from_text(text, dictionary, default="Not specified"):
    text = text.lower()
    for key, terms in dictionary.items():
        if any(term in text for term in terms):
            return key
    return default


def infer_metabolic_process(name):
    lname = name.lower()
    for process, terms in METABOLIC_PROCESSES.items():
        if any(t in lname for t in terms):
            return process
    return "Not available"


def infer_role(name):
    lname = name.lower()
    if lname.startswith("dl-") or lname.endswith("ol"):
        return "Derivative"
    if any(x in lname for x in ["glut", "arg", "lys", "phe", "trypt"]):
        return "Intermediate"
    return "Not determined"


def scholar_link(name):
    return f"https://scholar.google.com/scholar?q={quote(name + ' placenta pregnancy')}"


# ---------------------------
# Literature search
# ---------------------------

def search_europe_pmc(name):
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query={quote(name + ' pregnancy placenta')}&format=json&pageSize=2"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        if data.get("hitCount", 0) == 0:
            return []

        return data["resultList"]["result"]

    except Exception:
        return []


# ---------------------------
# Core analysis
# ---------------------------

def analyze_metabolite(name):
    hits = search_europe_pmc(name)
    process = infer_metabolic_process(name)
    role = infer_role(name)

    paper_titles = []
    organ = "Not specified"
    species = "Not specified"
    evidence_type = "None"

    for hit in hits:
        text = (hit.get("title", "") + " " + hit.get("abstractText", "")).lower()

        paper_titles.append(hit.get("title", ""))

        if any(t in text for t in PLACENTA_TERMS):
            evidence_type = "Direct"

        organ = detect_from_text(text, ORGANS, organ)
        species = detect_from_text(text, SPECIES, species)

    if evidence_type == "None" and process != "Not available":
        evidence_type = "Indirect"

    return {
        "Metabolite": name,
        "Metabolic_Process": process,
        "Role": role,
        "Paper_Title_1": paper_titles[0] if len(paper_titles) > 0 else "Not found",
        "Paper_Title_2": paper_titles[1] if len(paper_titles) > 1 else "Not found",
        "Pregnancy_Organ": organ,
        "Species": species,
        "Evidence_Type": evidence_type,
        "Google_Scholar_Link": scholar_link(name)
    }


def analyze_excel(file_path):
    df = pd.read_excel(file_path)
    names = df.iloc[:, 0].dropna().tolist()

    results = [analyze_metabolite(str(n)) for n in names]

    out_df = pd.DataFrame(results)
    output_path = "analysis_output.xlsx"
    out_df.to_excel(output_path, index=False)

    return output_path
