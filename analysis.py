# analysis.py

import os
import re
import fitz  # PyMuPDF
import easyocr
from PIL import Image
import pytesseract

# -----------------------------
# CONFIG
# -----------------------------

IMAGE_DIR = "extracted_images"
GENE_PATTERN = r"\b[A-Z0-9\-]{2,10}\b"   # Adjust if needed

# Initialize OCR reader once (important for speed)
reader = easyocr.Reader(['en'], gpu=False)


# -----------------------------
# 1️⃣ Extract PDF Text
# -----------------------------

def extract_pdf_text(pdf_path):
    text_content = ""

    doc = fitz.open(pdf_path)

    for page in doc:
        text_content += page.get_text()

    return text_content


# -----------------------------
# 2️⃣ Extract Images from PDF
# -----------------------------

def extract_images_from_pdf(pdf_path, output_folder=IMAGE_DIR):

    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):

            xref = img[0]
            base_image = doc.extract_image(xref)

            # Skip tiny images (icons/logos)
            if base_image["width"] < 300:
                continue

            image_bytes = base_image["image"]

            image_path = os.path.join(
                output_folder,
                f"page{page_index+1}_img{img_index+1}.png"
            )

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            image_paths.append(image_path)

    return image_paths


# -----------------------------
# 3️⃣ OCR Functions
# -----------------------------

def ocr_image_easyocr(image_path):
    """
    Primary OCR method (better for scientific figures)
    """
    try:
        results = reader.readtext(image_path, detail=0)
        return " ".join(results)
    except:
        return ""


def ocr_image_tesseract(image_path):
    """
    Backup OCR (lighter)
    """
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except:
        return ""


# -----------------------------
# 4️⃣ OCR All Images
# -----------------------------

def extract_text_from_images(image_paths):

    full_text = ""

    for img_path in image_paths:

        print(f"OCR processing: {img_path}")

        text = ocr_image_easyocr(img_path)

        # Fallback if EasyOCR fails
        if len(text.strip()) == 0:
            text = ocr_image_tesseract(img_path)

        full_text += "\n" + text

    return full_text


# -----------------------------
# 5️⃣ Gene Extraction
# -----------------------------

def extract_genes(text):

    matches = re.findall(GENE_PATTERN, text)

    # Filter common false positives
    blacklist = {
        "FIG", "DNA", "RNA", "ATP",
        "PDF", "SUPP", "ET", "AL"
    }

    genes = sorted(set(
        g for g in matches
        if g not in blacklist
        and not g.isdigit()
    ))

    return genes


# -----------------------------
# 6️⃣ Full Pipeline
# -----------------------------

def analyze_pdf(pdf_path):

    print("Step 1: Extracting PDF text...")
    pdf_text = extract_pdf_text(pdf_path)

    print("Step 2: Extracting images...")
    image_paths = extract_images_from_pdf(pdf_path)

    print(f"Found {len(image_paths)} images")

    print("Step 3: Running OCR...")
    image_text = extract_text_from_images(image_paths)

    print("Step 4: Merging text...")
    full_text = pdf_text + "\n" + image_text

    print("Step 5: Extracting genes...")
    genes = extract_genes(full_text)

    return {
        "total_genes": len(genes),
        "genes": genes
    }


# -----------------------------
# CLI TEST (Optional)
# -----------------------------

if __name__ == "__main__":

    pdf_file = "sample.pdf"  # Replace with your file

    results = analyze_pdf(pdf_file)

    print("\n===== RESULTS =====")
    print(f"Total genes found: {results['total_genes']}")
    print(results["genes"])
