import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil

from analysis import analyze_all   # ← This now exists


app = FastAPI()

UPLOAD_FOLDER = "uploads"
OUTPUT_FILE = "analysis_results.xlsx"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Placenta Literature Analyzer Running"}


# -------------------------------
# FILE UPLOAD
# -------------------------------
@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):

    for file in files:

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    return {"message": "Files uploaded successfully"}


# -------------------------------
# RUN ANALYSIS
# -------------------------------
@app.get("/analyze/")
def run_analysis():

    output_path = analyze_all(UPLOAD_FOLDER, OUTPUT_FILE)

    return FileResponse(
        output_path,
        filename="analysis_results.xlsx"
    )
