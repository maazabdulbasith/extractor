import re
from typing import List, Dict

def extract_transactions(lines: List[str]) -> List[Dict]:
    """
    Extracts transactions from bank statement lines.
    Assumes typical format: DATE | DESCRIPTION | DEBIT | CREDIT | BALANCE
    """

    transactions = []

    # Regex patterns (can adjust based on your statement format)
    date_pattern = r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b"   # e.g. 12/08/2025 or 12-08-25
    amount_pattern = r"[\d,]+\.\d{2}"                       # e.g. 1,234.56

    for line in lines:
        # Try to detect a transaction row
        date_match = re.search(date_pattern, line)
        amounts = re.findall(amount_pattern, line)

        if date_match and amounts:
            date = date_match.group(1)
            
            # Last amount is usually balance
            balance = amounts[-1]

            # If 2 amounts → debit & balance  OR  credit & balance
            debit, credit = None, None
            if len(amounts) == 2:
                # Heuristic: if line contains "DR" → debit
                if "DR" in line.upper():
                    debit = amounts[0]
                else:
                    credit = amounts[0]

            # If 3 amounts → debit, credit, balance
            elif len(amounts) == 3:
                debit, credit, balance = amounts

            # Description = everything between date and first amount
            try:
                parts = line.split(date)[1]
                description = parts.split(amounts[0])[0].strip()
            except:
                description = "N/A"

            transactions.append({
                "date": date,
                "description": description,
                "debit": debit,
                "credit": credit,
                "balance": balance
            })

    return transactions
