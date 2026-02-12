import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

# ==============================
# CONFIG — TUNE PERFORMANCE HERE
# ==============================

USE_OCR = True              # Toggle OCR ON/OFF
MAX_IMAGES_PER_PDF = 5     # Limit OCR images
MIN_IMAGE_SIZE = 300       # Skip tiny figures
DOWNSCALE_FACTOR = 2       # Reduce OCR resolution

OUTPUT_FILE = "analysis_results.xlsx"


# ==============================
# TEXT EXTRACTION
# ==============================

def extract_text_from_pdf(pdf_path):
    print(f"[TEXT] Opening: {pdf_path}")

    doc = fitz.open(pdf_path)
    full_text = ""

    for page_num, page in enumerate(doc):
        print(f"[TEXT] Page {page_num + 1}")
        full_text += page.get_text()

    return full_text


# ==============================
# IMAGE + OCR EXTRACTION
# ==============================

def extract_ocr_from_pdf(pdf_path):
    if not USE_OCR:
        print("[OCR] Skipped (disabled)")
        return ""

    print(f"[OCR] Processing images in: {pdf_path}")

    doc = fitz.open(pdf_path)
    ocr_text = ""
    image_count = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images(full=True)

        print(f"[OCR] Page {page_index + 1} → {len(image_list)} images found")

        for img_index, img in enumerate(image_list):

            if image_count >= MAX_IMAGES_PER_PDF:
                print("[OCR] Image limit reached")
                return ocr_text

            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            image = Image.open(io.BytesIO(image_bytes))

            # Skip small images
            if image.width < MIN_IMAGE_SIZE or image.height < MIN_IMAGE_SIZE:
                print("[OCR] Skipping small image")
                continue

            # Downscale
            image = image.resize(
                (image.width // DOWNSCALE_FACTOR,
                 image.height // DOWNSCALE_FACTOR)
            )

            print(f"[OCR] Running OCR on image {image_count + 1}")

            text = pytesseract.image_to_string(image)
            ocr_text += text + "\n"

            image_count += 1

    return ocr_text


# ==============================
# GENE / METABOLITE DETECTION
# ==============================

def detect_entities(text):

    # Example keywords — replace with your database
    keywords = [
        "glucose",
        "lactate",
        "serine",
        "glycine",
        "placenta",
        "metabolism",
        "ATP",
        "mitochondria"
    ]

    found = []

    for word in keywords:
        if word.lower() in text.lower():
            found.append(word)

    return found


# ==============================
# SINGLE PDF PIPELINE
# ==============================

def process_pdf(pdf_path):

    print(f"\n=== Processing: {os.path.basename(pdf_path)} ===")

    text_data = extract_text_from_pdf(pdf_path)
    ocr_data = extract_ocr_from_pdf(pdf_path)

    combined_text = text_data + "\n" + ocr_data

    entities = detect_entities(combined_text)

    return {
        "paper": os.path.basename(pdf_path),
        "entities_found": ", ".join(entities) if entities else "Not Found"
    }


# ==============================
# MAIN ANALYSIS FUNCTION
# ==============================

def run_analysis(pdf_folder):

    pdf_files = [
        os.path.join(pdf_folder, f)
        for f in os.listdir(pdf_folder)
        if f.endswith(".pdf")
    ]

    print(f"\nFound {len(pdf_files)} PDFs\n")

    # Parallel processing
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(process_pdf, pdf_files))

    df = pd.DataFrame(results)

    df.to_excel(OUTPUT_FILE, index=False)

    print(f"\n✅ Analysis complete → {OUTPUT_FILE}")


# ==============================
# ENTRY POINT
# ==============================

if __name__ == "__main__":

    PDF_FOLDER = "pdfs"   # Folder containing uploaded papers

    run_analysis(PDF_FOLDER)
