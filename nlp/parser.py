import re

def parse_bank_statement(text):
    """
    Parse raw bank statement text into structured JSON.
    Example: [{"date": "01-08-2025", "description": "...", "debit": "40.00", "credit": None, "balance": "45.09"}]
    """

    transactions = []
    lines = text.splitlines()

    # Example regex for Indian bank statements (adjust as needed)
    pattern = re.compile(
        r"(?P<date>\d{2}-\d{2}-\d{4})\s+"
        r"(?P<description>.+?)\s+"
        r"(?P<debit>\d+\.\d{2}|-)?\s*"
        r"(?P<credit>\d+\.\d{2}|-)?\s*"
        r"(?P<balance>\d+\.\d{2})"
    )

    for line in lines:
        match = pattern.search(line)
        if match:
            transactions.append({
                "date": match.group("date"),
                "description": match.group("description").strip(),
                "debit": match.group("debit") if match.group("debit") != "-" else None,
                "credit": match.group("credit") if match.group("credit") != "-" else None,
                "balance": match.group("balance"),
            })

    return transactions
