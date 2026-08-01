"""
Header parsing logic for snapshot files.

Extracts label/value pairs from the header rows of snapshot files.
"""

from typing import List, Tuple
import pandas as pd

from domain.constants import HEADER_LABELS


def parse_header(df: pd.DataFrame, max_rows: int = 5) -> List[Tuple[str, str]]:
    """
    Parse up to the first `max_rows` rows as 2-column label/value pairs.
    
    Args:
        df: Raw DataFrame loaded from file
        max_rows: Maximum number of rows to scan for header info
        
    Returns:
        Ordered list of (label, value) tuples
    """
    results = []
    if df is None or df.empty:
        return results

    nrows = min(max_rows, df.shape[0])
    for r in range(nrows):
        # Stop if we hit the table row containing "frame"
        try:
            label_raw = str(df.iat[r, 0]).strip()
        except Exception:
            label_raw = ""
        if label_raw and label_raw.lower() == "frame":
            break

        # Pull the value column
        try:
            value = str(df.iat[r, 1]).strip()
        except Exception:
            value = ""

        # Skip truly empty/NaN-ish rows
        if not label_raw or label_raw.lower() == "nan":
            continue

        # Check if ":" is in the label and split it
        if ":" in label_raw:
            parts = label_raw.split(":", 1)
            if len(parts) == 2:
                potential_value = parts[1].strip()
                label_raw = parts[0].strip()
                if potential_value:
                    value = potential_value

        # Check for standalone date in label column (value is empty)
        if (not value or value.lower() == "nan" or value.lower() == "none") and len(label_raw) > 8:
            if _is_date_string(label_raw):
                value = label_raw
                label_raw = "Date / Time"

        if not value or value.lower() == "nan":
            continue

        label = _normalize_label(label_raw)
        results.append((label, value))

    return results


def find_date_time(header_list: List[Tuple[str, str]]) -> str:
    """
    Find the date/time value in the header list.
    
    Args:
        header_list: List of (label, value) tuples from parse_header
        
    Returns:
        Date/time string if found, empty string otherwise
    """
    for label, value in header_list:
        if label == "Date / Time":
            return value
    return ""


def _normalize_label(text: str) -> str:
    """
    Normalize a label to a canonical display name if recognized.
    Uses exact, case-insensitive matching with minor spacing/punctuation tolerance.
    """
    if not text:
        return ""
    raw = text.strip().lower()
    
    # Quick exact lookup
    if raw in HEADER_LABELS:
        return HEADER_LABELS[raw]

    # Light fuzzy: remove punctuation/spaces to catch variations
    squished = "".join(ch for ch in raw if ch.isalnum())
    for k, v in HEADER_LABELS.items():
        k_squished = "".join(ch for ch in k if ch.isalnum())
        if squished == k_squished:
            return v

    # Fall back to original as-is if unknown
    return text.strip()


def _is_date_string(text: str) -> bool:
    """Check if a string appears to be a date/time value."""
    try:
        pd.to_datetime(text)
        return True
    except (ValueError, TypeError):
        pass
    
    # Try normalizing (handles formats like "Nov 21 2025/13.20.57")
    try:
        normalized = text.replace("/", " ").replace(".", ":")
        pd.to_datetime(normalized)
        return True
    except (ValueError, TypeError):
        pass
    
    # Try explicit format as fallback
    try:
        pd.to_datetime(text, format="%b %d %Y/%H.%M.%S")
        return True
    except (ValueError, TypeError):
        pass
    
    return False
