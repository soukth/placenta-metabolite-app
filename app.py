from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import pandas as pd
import uuid
import os
import time
from analysis import analyze_all
app = FastAPI()

RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# ---------------------------
# MOCK ANALYSIS (replace with your real logic)
# ---------------------------
def run_analysis(df):
    time.sleep(1)  # simulate processing
    results = []

    for gene in df.iloc[:, 0].astype(str):
        results.append({
            "Gene": gene,
            "PubMed_DOI": "Not found",
            "EuropePMC_DOI": "Not found",
            "Evidence_Type": "None",
            "Pathway": "Not available",
            "Pathway_Placenta_Evidence": "Not available"
        })

    return pd.DataFrame(results)

# ---------------------------
# ROUTES
# ---------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())

    df = pd.read_excel(file.file)


    result_df = analyze_all(df)

    output_path = f"{RESULTS_DIR}/{job_id}.xlsx"
    result_df.to_excel(output_path, index=False)

    result_df.to_json(f"{RESULTS_DIR}/{job_id}.json", orient="records")

    return {"job_id": job_id}

@app.get("/evidence/{job_id}")
def get_evidence(job_id: str):
    path = f"{RESULTS_DIR}/{job_id}.json"
    if not os.path.exists(path):
        return JSONResponse({"error": "Job not found"}, status_code=404)

    df = pd.read_json(path)
    return df[["Gene", "PubMed_DOI", "EuropePMC_DOI", "Evidence_Type"]].to_dict(orient="records")

@app.get("/pathways/{job_id}")
def get_pathways(job_id: str):
    path = f"{RESULTS_DIR}/{job_id}.json"
    if not os.path.exists(path):
        return JSONResponse({"error": "Job not found"}, status_code=404)

    df = pd.read_json(path)
    return df[["Gene", "Pathway", "Pathway_Placenta_Evidence"]].to_dict(orient="records")

@app.get("/download/{job_id}")
def download(job_id: str):
    path = f"{RESULTS_DIR}/{job_id}.xlsx"
    if not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(path, filename="analysis_results.xlsx")

