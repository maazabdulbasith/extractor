import csv
from datetime import datetime
from typing import List, Dict, Iterable
import io
import re


def _decode_bytes(data: bytes) -> str:
    for enc in ('utf-8-sig', 'utf-16', 'cp1252', 'latin-1'):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode('utf-8', errors='ignore')


def _read_text(file_obj) -> str:
    if isinstance(file_obj, (io.TextIOBase,)):
        return file_obj.read()
    data = file_obj.read()
    if isinstance(data, str):
        return data
    return _decode_bytes(data or b"")


def _canonical_key(key: str) -> str:
    k = (key or '').strip().lower().lstrip('\ufeff')
    return k


def _pick_header(fieldnames: List[str], candidates: List[str]) -> str:
    canon_to_orig = { _canonical_key(fn): fn for fn in (fieldnames or []) }
    for cand in candidates:
        if cand in canon_to_orig:
            return canon_to_orig[cand]
    return ''


def extract_text_from_csv(file_obj) -> List[Dict]:
    text = _read_text(file_obj)
    if not text:
        return []

    try:
        sample = text[:4096]
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except Exception:
        dialect = csv.excel
        dialect.delimiter = ','

    sio = io.StringIO(text)
    reader = csv.DictReader(sio, dialect=dialect)

    date_keys = ['date', 'transaction date', 'txn date']
    narration_keys = ['narration', 'description', 'details', 'particulars', 'remarks', 'chq/ref no', 'chq/ref', 'ref no']
    debit_keys = ['debit', 'withdrawal', 'debits', 'dr', 'amount debit', 'withdrawal(dr)']
    credit_keys = ['credit', 'deposit', 'cr', 'credits', 'amount credit', 'deposit(cr)']
    balance_keys = ['balance', 'running balance', 'closing balance', 'available balance']

    field_map: Dict[str, str] = {}
    if reader.fieldnames:
        field_map['date'] = _pick_header(reader.fieldnames, date_keys)
        field_map['narration'] = _pick_header(reader.fieldnames, narration_keys)
        field_map['debit'] = _pick_header(reader.fieldnames, debit_keys)
        field_map['credit'] = _pick_header(reader.fieldnames, credit_keys)
        field_map['balance'] = _pick_header(reader.fieldnames, balance_keys)

    transactions: List[Dict] = []

    date_formats = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%b-%Y', '%d %b %Y', '%d/%m/%y', '%d-%m-%y']

    def parse_date(s: str):
        s = (s or '').strip()
        for fmt in date_formats:
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None

    def to_float(s: str) -> float:
        s = (s or '').replace(',', '').replace('₹', '').replace('INR', '').strip()
        s = s.replace('DR', '').replace('Dr', '').replace('Cr', '').replace('CR', '').strip()
        try:
            return float(s) if s else 0.0
        except ValueError:
            return 0.0

    # Primary path: header-based
    has_min_headers = bool(field_map.get('date')) and bool(field_map.get('balance'))
    if has_min_headers:
        for row in reader:
            date_field = field_map.get('date') or 'Date'
            narration_field = field_map.get('narration') or 'Narration'
            debit_field = field_map.get('debit') or 'Debit'
            credit_field = field_map.get('credit') or 'Credit'
            balance_field = field_map.get('balance') or 'Balance'

            date_val = parse_date(row.get(date_field, ''))
            if not date_val:
                continue

            narration = (row.get(narration_field, '') or '').strip()
            debit_str = row.get(debit_field, '') or ''
            credit_str = row.get(credit_field, '') or ''
            balance_str = row.get(balance_field, '') or ''

            transactions.append({
                'date': date_val,
                'narration': narration,
                'debit': to_float(debit_str),
                'credit': to_float(credit_str),
                'balance': to_float(balance_str),
            })
        if transactions:
            return transactions

    # Fallback: positional parsing (skip preamble until first date-like row)
    sio2 = io.StringIO(text)
    raw_reader = csv.reader(sio2, dialect=dialect)

    date_regex = re.compile(r"^\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s*$")
    started = False

    for row in raw_reader:
        if not row or all((c or '').strip() == '' for c in row):
            continue
        if not started:
            first = (row[0] if len(row) > 0 else '').strip()
            if date_regex.match(first):
                started = True
            else:
                continue
        # Now in data section; each row should start with a date
        first = (row[0] if len(row) > 0 else '').strip()
        if not date_regex.match(first):
            continue
        date_val = parse_date(first)
        if not date_val:
            continue

        # Collect narration from middle textual columns
        middle_cols = row[1:-1] if len(row) >= 3 else row[1:]
        narration_parts = []
        for c in middle_cols:
            cs = (c or '').strip()
            if not cs:
                continue
            if re.search(r"[\d]+[\d,]*\.?\d*\s*(CR|Cr|DR|Dr)?$", cs):
                continue
            narration_parts.append(cs)
        narration = ' '.join(narration_parts).strip()

        # Find numeric amounts and classify
        nums = []
        for c in row:
            cs = (c or '').strip()
            if re.search(r"\d", cs):
                m = re.search(r"([\d,]+\.?\d*)\s*(CR|Cr|DR|Dr)?", cs)
                if m:
                    val = to_float(m.group(1) + (m.group(2) or ''))
                    marker = (m.group(2) or '').upper()
                    nums.append((val, marker, cs))
        balance = 0.0
        debit = 0.0
        credit = 0.0
        if nums:
            balance = nums[-1][0]
            # look for explicit DR/CR
            for val, marker, cs in nums[:-1]:
                if marker == 'DR':
                    debit = val
                elif marker == 'CR':
                    credit = val
            # if not found, use heuristics: first amount is txn, sign by keywords
            if debit == 0.0 and credit == 0.0 and len(nums) >= 2:
                txn_val = nums[0][0]
                line_text = ' '.join(row).upper()
                if 'DR' in line_text or 'WITHDRAW' in line_text:
                    debit = txn_val
                else:
                    credit = txn_val

        transactions.append({
            'date': date_val,
            'narration': narration,
            'debit': debit,
            'credit': credit,
            'balance': balance,
        })

    return transactions 