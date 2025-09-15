import argparse
import json
from extractor.pdf_extractor import extract_text_from_pdf
from nlp.preprocess import clean_text, tokenize_lines
from nlp.rule_extractor import extract_transactions


def main():
    parser = argparse.ArgumentParser(description="Run extraction on a PDF file")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()

    raw_text = extract_text_from_pdf(args.pdf_path)
    cleaned_text = clean_text(raw_text)
    lines = tokenize_lines(cleaned_text)
    transactions = extract_transactions(lines)

    print(json.dumps(transactions[:5], indent=2))


if __name__ == "__main__":
    main()
