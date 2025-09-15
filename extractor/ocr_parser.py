import pytesseract
import cv2
from PIL import Image

def extract_text_from_image(img_path: str) -> str:
    """
    Extracts text from an image (JPG/PNG) using Tesseract OCR.
    Applies preprocessing for better accuracy.
    """
    # Load image
    img = cv2.imread(img_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Thresholding (remove noise, improve contrast)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # OCR with Tesseract
    text = pytesseract.image_to_string(thresh, lang="eng")
    return text.strip()

def extract_text_from_scanned_pdf(pdf_path: str) -> str:
    """
    Extracts text from a scanned PDF using OCR on each page.
    Requires pdf2image to convert PDF pages into images.
    """
    from pdf2image import convert_from_path

    pages = convert_from_path(pdf_path)
    text = ""

    for page in pages:
        text += pytesseract.image_to_string(page, lang="eng") + "\n"

    return text.strip()
