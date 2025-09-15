import re
from datetime import datetime


def normalize_text(text: str) -> list[str]:
    """
    Clean up extracted PDF/scan text into usable lines for parsing.
    - Replaces multiple spaces with one
    - Forces line breaks before dates
    - Splits into clean lines
    """
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Insert newline before dates (dd-mm-yyyy)
    text = re.sub(r'(\d{2}-\d{2}-\d{4})', r'\n\1', text)

    # Split and strip
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return lines


def parse_bank_statement(text: str):
    """
    Parse raw bank statement text into structured transactions.
    Returns a list of dicts like:
    [
        {
            'date': date(2025, 8, 1),
            'narration': 'UPI/XYZ/12345',
            'debit': 40.00,
            'credit': 0.00,
            'balance': 500.00
        },
        ...
    ]
    """
    transactions = []
    lines = normalize_text(text)

    for line in lines:
        # Regex pattern to capture date, narration, debit, credit, balance
        match = re.match(
            r'(?P<date>\d{2}-\d{2}-\d{4})\s+'
            r'(?P<narration>.+?)\s+'
            r'(?P<debit>[\d,]+\.\d{2})?\s*'
            r'(?P<credit>[\d,]+\.\d{2})?\s*'
            r'(?P<balance>[\d,]+\.\d{2})',
            line
        )

        if match:
            txn = match.groupdict()

            # Convert date
            txn['date'] = datetime.strptime(txn['date'], '%d-%m-%Y').date()

            # Convert to float safely
            for key in ['debit', 'credit', 'balance']:
                if txn[key]:
                    txn[key] = float(txn[key].replace(',', ''))
                else:
                    txn[key] = 0.0

            transactions.append(txn)

    return transactions
