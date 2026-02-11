import os
import re
import fitz  # PyMuPDF
import easyocr
import pandas as pd
from PIL import Image
import pytesseract

# ----------------------------------
# CONFIG
# ----------------------------------

IMAGE_DIR = "extracted_images"
OUTPUT_EXCEL = "analysis_results.xlsx"

GENE_PATTERN = r"\b[A-Z0-9\-]{2,10}\b"

BLACKLIST = {
    "FIG", "DNA", "RNA", "ATP",
    "PDF", "SUPP", "ET", "AL"
}

# Initialize OCR reader
reader = easyocr.Reader(['en'], gpu=False)


# ----------------------------------
# 1️⃣ Extract PDF Text
# ----------------------------------

def extract_pdf_text(pdf_path):

    text_content = ""
    doc = fitz.open(pdf_path)

    for page in doc:
        text_content += page.get_text()

    return text_content


# ----------------------------------
# 2️⃣ Extract Images
# ----------------------------------

def extract_images_from_pdf(pdf_path):

    os.makedirs(IMAGE_DIR, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):

            xref = img[0]
            base_image = doc.extract_image(xref)

            if base_image["width"] < 300:
                continue

            image_bytes = base_image["image"]

            image_path = os.path.join(
                IMAGE_DIR,
                f"page{page_index+1}_img{img_index+1}.png"
            )

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            image_paths.append(image_path)

    return image_paths


# ----------------------------------
# 3️⃣ OCR Images
# ----------------------------------

def ocr_images(image_paths):

    full_text = ""

    for img in image_paths:

        print(f"OCR processing: {img}")

        try:
            result = reader.readtext(img, detail=0)
            text = " ".join(result)

            if len(text.strip()) == 0:
                text = pytesseract.image_to_string(Image.open(img))

        except:
            text = ""

        full_text += "\n" + text

    return full_text


# ----------------------------------
# 4️⃣ Gene Extraction + Frequency
# ----------------------------------

def extract_gene_frequency(text):

    matches = re.findall(GENE_PATTERN, text)

    genes = [
        g for g in matches
        if g not in BLACKLIST
        and not g.isdigit()
    ]

    freq_dict = {}

    for g in genes:
        freq_dict[g] = freq_dict.get(g, 0) + 1

    return freq_dict


# ----------------------------------
# 5️⃣ Figure Gene Tagging
# ----------------------------------

def tag_figure_genes(pdf_freq, image_freq):

    all_genes = set(pdf_freq.keys()) | set(image_freq.keys())

    records = []

    for gene in all_genes:

        pdf_count = pdf_freq.get(gene, 0)
        img_count = image_freq.get(gene, 0)

        total = pdf_count + img_count

        found_in_fig = "Yes" if img_count > 0 else "No"

        records.append({
            "Gene": gene,
            "Frequency": total,
            "Found_In_Figures": found_in_fig
        })

    return records


# ----------------------------------
# 6️⃣ Dummy Evidence + Pathway
# (You already had APIs — keeping placeholder)
# ----------------------------------

def add_external_annotations(df):

    df["PubMed_DOI"] = "Not found"
    df["EuropePMC_DOI"] = "Not found"

    df["Scholar_Link"] = df["Gene"].apply(
        lambda g: f"https://scholar.google.com/scholar?q={g}"
    )

    # Pathway placeholder logic
    df["Pathway"] = "Not available"

    return df


# ----------------------------------
# 7️⃣ Full Pipeline
# ----------------------------------

def analyze_pdf(pdf_path):

    print("Step 1: Extracting PDF text...")
    pdf_text = extract_pdf_text(pdf_path)

    print("Step 2: Extracting images...")
    image_paths = extract_images_from_pdf(pdf_path)

    print(f"Images found: {len(image_paths)}")

    print("Step 3: OCR processing...")
    image_text = ocr_images(image_paths)

    print("Step 4: Gene frequency (PDF)...")
    pdf_freq = extract_gene_frequency(pdf_text)

    print("Step 5: Gene frequency (Images)...")
    image_freq = extract_gene_frequency(image_text)

    print("Step 6: Tagging figure genes...")
    records = tag_figure_genes(pdf_freq, image_freq)

    df = pd.DataFrame(records)

    print("Step 7: Adding annotations...")
    df = add_external_annotations(df)

    print("Step 8: Sorting...")
    df = df.sort_values(by="Frequency", ascending=False)

    print("Step 9: Saving Excel...")
    df.to_excel(OUTPUT_EXCEL, index=False)

    print(f"\n✅ Done — saved to {OUTPUT_EXCEL}")

    return df


# ----------------------------------
# CLI TEST
# ----------------------------------

if __name__ == "__main__":

    pdf_file = "sample.pdf"  # Replace

    analyze_pdf(pdf_file)
