from .pdf_parser import extract_text_from_pdf
from .ocr_parser import extract_text_from_scanned_pdf

def extract_text(pdf_path: str) -> str:
    """
    Extract text from a PDF.
    - First tries pdfplumber (digital PDF).
    - If no text found, falls back to OCR (scanned PDF).
    """
    text = extract_text_from_pdf(pdf_path)
    if not text or len(text.split()) < 5:  # if too little text, assume scanned
        text = extract_text_from_scanned_pdf(pdf_path)
    return text
