import re
from typing import Union, Optional

def parse_currency_amount(raw_value: Union[str, int, float, None], currency: str = "COP") -> float:
    """
    Parses a user input or database value into a clean float, handling
    currency-specific thousand/decimal separators safely without corrupting decimals.
    
    - For USD: preserves decimal points (e.g., '12.50', '1,250.75' -> 1250.75).
      If a user inputs comma as decimal separator (e.g., '12,50'), converts to 12.50.
    - For COP: amounts are generally integers with dots or commas as thousand separators
      (e.g., '45.000', '45,000' -> 45000.0). Preserves explicit cent decimals if present.
    """
    if raw_value is None:
        return 0.0
    if isinstance(raw_value, (int, float)):
        return float(raw_value)
    
    val = str(raw_value).strip()
    if not val:
        return 0.0
    
    # Handle negative sign
    is_negative = False
    if val.startswith("-"):
        is_negative = True
        val = val[1:].strip()
    
    # Remove currency symbols or extra spaces
    val = val.replace("$", "").replace("USD", "").replace("usd", "").replace("COP", "").replace("cop", "").strip()
    
    currency_upper = (currency or "COP").upper().strip()
    
    if currency_upper == "USD":
        if "," in val and "." in val:
            if val.find(",") < val.find("."):
                # Standard US: 1,250.50
                val = val.replace(",", "")
            else:
                # European/Latin: 1.250,50
                val = val.replace(".", "").replace(",", ".")
        elif "," in val:
            parts = val.split(",")
            if len(parts) == 2 and len(parts[1]) in (1, 2):
                val = val.replace(",", ".")
            else:
                val = val.replace(",", "")
        try:
            result = round(float(val), 2)
        except ValueError:
            result = 0.0
    else:
        # COP mode
        if "," in val and "." in val:
            if val.find(".") < val.find(","):
                val = val.replace(".", "").replace(",", ".")
            else:
                val = val.replace(",", "")
        elif "." in val and "," not in val:
            parts = val.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                # Exactly 3 digits: e.g. 50.000
                val = val.replace(".", "")
            elif len(parts) > 2:
                # E.g. 1.000.000
                val = val.replace(".", "")
            else:
                # E.g. 45000.5 or 45.5 -> keep as float
                pass
        elif "," in val and "." not in val:
            parts = val.split(",")
            if len(parts) == 2 and len(parts[1]) in (1, 2):
                val = val.replace(",", ".")
            else:
                val = val.replace(",", "")
        
        try:
            result = float(val)
        except ValueError:
            result = 0.0

    return -result if is_negative else result
