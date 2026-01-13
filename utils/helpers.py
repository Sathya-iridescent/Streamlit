"""
Helper utility functions
"""
from datetime import datetime, timedelta


def calc_delivery_minus_4(date_str: str) -> str:
    """Delivery date = extracted date - 4 days (always)."""
    try:
        d = datetime.strptime(date_str, "%d.%m.%Y")
        d -= timedelta(days=4)
        return d.strftime("%d.%m.%Y")
    except Exception:
        return date_str  # fallback


def calc_delivery_month(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%d.%m.%Y")
        return d.strftime("%B")
    except Exception:
        return ""


def calc_no_of_boxes(caselot, qty) -> int:
    try:
        c = int(caselot)
        q = int(qty)
        return q // c if c > 0 else 0
    except Exception:
        return 0


def calc_ex_factory(location: str, delv_date_str: str) -> str:
    """
    Ex-Factory Date = (Delivery Date AFTER -4 days) minus location-based days:
      Vadodara -> -6 days
      Bhiwandi -> -4 days
      Mandal / Isnapur / Medak / Manoharabad  -> -3 days
      Others -> same as delivery date
    """
    try:
        d = datetime.strptime(delv_date_str, "%d.%m.%Y")
    except Exception:
        return ""

    loc = (location or "").lower()
    days = 0
    if "vadodara" in loc:
        days = 6
    elif "bhiwandi" in loc:
        days = 4
    elif "mandal" in loc or "isnapur" in loc or "medak" in loc or "manoharabad" in loc:
        days = 3

    d -= timedelta(days=days)
    return d.strftime("%d.%m.%Y")


def parse_exfactory_date_for_sort(date_str):
    """
    Parse Ex-Factory Date string (dd.mm.yyyy) to datetime object for sorting.
    Returns datetime object or None if parsing fails.
    """
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y")
    except Exception:
        return None


def calculate_exfactory_flag(date_str):
    """
    Returns: 'overdue' / 'due-soon' / '' based on ex-factory date.
    - 'overdue': Today and all past dates (RED)
    - 'due-soon': Next 3 days after today (1, 2, 3 days from today) → YELLOW
    - '': Future dates beyond 3 days → Normal
    """
    if not date_str or date_str.strip() == "":
        return ""
    try:
        # Parse date in format dd.mm.yyyy
        d = datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
        today = datetime.today().date()

        # Calculate days difference (positive = future, negative = past)
        days_diff = (d - today).days
        
        # Today and all past dates → RED (overdue)
        if days_diff <= 0:
            return "overdue"
        
        # Next 3 days after today (1, 2, 3 days from today) → YELLOW (due-soon)
        if 1 <= days_diff <= 3:
            return "due-soon"
        
        # Future dates beyond 3 days → Normal (no highlighting)
        return ""
    except Exception as e:
        # If date parsing fails, return empty (no highlighting)
        print(f"Error parsing date '{date_str}': {e}")
        return ""

