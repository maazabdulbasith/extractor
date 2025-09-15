import pdfplumber

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a digital PDF using pdfplumber.
    Works only if the PDF contains selectable text.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text.strip()
