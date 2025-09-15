import re
from datetime import datetime

def clean_text(raw_text: str) -> str:
    """
    Clean unwanted characters, headers, and footers.
    """
    lines = raw_text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip common bank headers/footers
        if any(keyword in line.lower() for keyword in [
            "statement", "page", "powered by", "confidential", "banking"
        ]):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def normalize_date(date_str: str) -> str:
    """
    Normalize date into YYYY-MM-DD format.
    Supports DD-MM-YYYY, DD/MM/YYYY, DD Mon YYYY, etc.
    """
    date_formats = ["%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%d %b %Y"]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # return as-is if no match


def normalize_amount(amount_str: str) -> float:
    """
    Normalize currency amounts by removing commas, ₹, and converting to float.
    """
    clean = re.sub(r"[₹,]", "", amount_str)
    try:
        return float(clean)
    except ValueError:
        return 0.0


def merge_multiline_transactions(lines: list) -> list:
    """
    Merge lines if a transaction description spills into multiple lines.
    A line starting without a date continues the previous transaction.
    """
    merged = []
    date_pattern = re.compile(r"\b\d{2}[-/]\d{2}[-/]\d{4}\b")

    for line in lines:
        if date_pattern.match(line.split()[0]):  # starts with a date
            merged.append(line)
        else:
            if merged:
                merged[-1] += " " + line  # append to last transaction

    return merged


def preprocess_text(raw_text: str) -> list:
    """
    Full preprocessing pipeline:
    - Clean text
    - Merge multi-line descriptions
    - Return list of transaction lines
    """
    cleaned = clean_text(raw_text)
    lines = cleaned.splitlines()
    merged_lines = merge_multiline_transactions(lines)
    return merged_lines

def tokenize_lines(text: str) -> list:
    return text.splitlines()
