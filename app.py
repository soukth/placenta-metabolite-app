from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import os
from analysis import analyze_excel

app = FastAPI()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

last_output = None


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Placenta Metabolite Analyzer</h2>
    <form action="/analyze" method="post" enctype="multipart/form-data">
      <input type="file" name="file">
      <button type="submit">Analyze</button>
    </form>
    <br>
    <a href="/download">Download Excel</a>
    """


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    global last_output

    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    last_output = analyze_excel(path)
    return {"status": "Analysis complete"}


@app.get("/download")
def download():
    if last_output:
        return FileResponse(last_output, filename="analysis_output.xlsx")
    return {"error": "No analysis run yet"}
