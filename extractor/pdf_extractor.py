import os
import tempfile
import logging
import numpy as np
import pdfplumber
import pytesseract
import cv2
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""

    # --- Step 1: Try pdfplumber (digital PDFs) ---
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text += page_text + "\n"

    if len(text.strip()) > 20:
        return text

    # --- Step 2: OCR fallback (scanned PDFs) ---
    logger.info("Falling back to OCR for file: %s", pdf_path)

    poppler_path = os.getenv("POPPLER_PATH")  # optional on Windows if not in PATH

    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(
            pdf_path,
            dpi=300,
            output_folder=temp_dir,
            poppler_path=poppler_path if poppler_path else None,
        )

        for i, img in enumerate(images):
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            text += pytesseract.image_to_string(thresh, lang="eng") + "\n"

    return text
