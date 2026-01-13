import fitz
import re
from typing import List, Dict


# --------------------------------------------------------
# CLEAN DESCRIPTION BEFORE HSN
# --------------------------------------------------------
def clean_description(desc: str) -> str:
    return re.sub(r'\s+', ' ', desc.split('[HSN')[0]).strip()


# --------------------------------------------------------
# FORMAT DETECTORS
# --------------------------------------------------------
def is_new_format(text: str) -> bool:
    # New 3-row DMART item format
    return bool(re.search(r'\n\s*\d{1,3}\s+\d{10}\s*\n\s*\d{2}\.\d{2}\.\d{4}', text))


def is_revised_format(text: str) -> bool:
    # Revised format: Sno + EAN + Delivery date, all in separate lines
    return bool(re.search(r'\n\s*\d{1,3}\s+\d{10}\s*\n\s*\d{2}\.\d{2}\.\d{4}\s*\n', text))


# --------------------------------------------------------
# REGEX PATTERNS
# --------------------------------------------------------

# New Format Pattern
new_pattern = re.compile(
    r'(\d{1,3})\s+'                    # Sno
    r'(\d{10})\s*'                     # EAN
    r'(\d{2}\.\d{2}\.\d{4})'           # Delivery Date
    r'(.*?)'                           # Description (multi-line)
    r'EA\s+'                           # Unit
    r'(\d+)\s+'                        # CaseLot
    r'(?:\d+\s+)?'                     # Optional Boxes
    r'(\d+)\s',                        # Quantity
    re.DOTALL
)

# Old Format Pattern
old_pattern = re.compile(
    r'(\d{1,3})\s+(\d{10}).*?(\d{2}\.\d{2}\.\d{4})\s*(.*?)'
    r'(?:\[IAP|\[HSN Code).*?(\d+)\s+(?:\d+)\s+(\d+)',
    re.DOTALL
)

# Revised PO Pattern  (your problematic file)
revised_pattern = re.compile(
    r'(\d{1,3})\s+'                     # Sno
    r'(\d{10})\s*'                      # EAN
    r'(\d{2}\.\d{2}\.\d{4})\s*'         # Delivery Date
    r'(.*?)'                            # Description (multi-line)
    r'EA\s+(\d+).*?'                    # CaseLot (first EA number)
    r'(\d+)\s+\d+\.\d{2}\s',            # Qty = number just before price (e.g. 2800 88.00)
    re.DOTALL
)



# --------------------------------------------------------
# HEADER EXTRACTION
# --------------------------------------------------------
def extract_header(text: str) -> tuple[str, str]:
    po_number, po_date = "N/A", "N/A"

    # PO #
    po_match = re.search(r'PO\s*#.*?(\d{10})', text, re.IGNORECASE | re.DOTALL)
    if po_match:
        po_number = po_match.group(1)

    # PO Date
    date_match = re.search(r'PO\s*Date.*?(\d{2}\.\d{2}\.\d{4})', text, re.IGNORECASE | re.DOTALL)
    if date_match:
        po_date = date_match.group(1)

    return po_number, po_date


# --------------------------------------------------------
# LOCATION EXTRACTION
# --------------------------------------------------------
def extract_location(text: str) -> str:
    t = text.lower()

    if "bhiwandi" in t or "sape" in t:
        return "Bhiwandi"

    if "isnapur" in t or "hyd" in t or "medak" in t:
        return "Medak"

    if "vadodara" in t or "baroda" in t or "horizon industrial park" in t:
        return "Vadodara"

    if "manoharabad" in t:
        return "Manoharabad"

    return "N/A"


# --------------------------------------------------------
# MAIN EXTRACTION LOGIC
# --------------------------------------------------------
def extract_items(text: str, filename: str) -> List[Dict[str, str]]:
    po, po_date = extract_header(text)
    location = extract_location(text)

    # Select correct pattern
    if is_revised_format(text):
        pattern = revised_pattern
    elif is_new_format(text):
        pattern = new_pattern
    else:
        pattern = old_pattern

    results = []

    for m in pattern.finditer(text):
        desc = clean_description(m.group(4))
        del_date = m.group(3)

        results.append({
            "Filename": filename,
            "PO #": po,
            "PO Date": po_date,
            "Location": location,
            "Delivery Date": del_date,
            "EAN NO": m.group(2),
            "Article Description": desc,
            "CaseLot": m.group(5),
            "Quantity": m.group(6)
        })

    # If nothing matched, add N/A row
    if not results:
        results.append({
            "Filename": filename,
            "PO #": po,
            "PO Date": po_date,
            "Location": location,
            "Delivery Date": "N/A",
            "EAN NO": "N/A",
            "Article Description": "N/A",
            "CaseLot": "N/A",
            "Quantity": "N/A"
        })

    return results
