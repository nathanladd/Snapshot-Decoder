import pandas as pd


# Standardize the labels found in the header. - labels we expect in row 0..3, col 0, with values in col 1.
CANON_LABELS = {
    "engine model": "Engine Model",
    "ecu map version": "ECU Map Version",
    "program sw version": "Program SW Version",
    "data logging": "Data Logging"
}

# Helper function for parse_simple_header
def _normalize_label(text: str) -> str:
    """
    Normalize a label to a canonical display name if recognized.
    Loosened matching: exact, case-insensitive; also allows minor spacing/punctuation differences.
    """
    if not text:
        return ""
    raw = text.strip().lower()
    # quick exact lookup
    if raw in CANON_LABELS:
        return CANON_LABELS[raw]

    # light fuzzy: remove punctuation/spaces to catch 'Program SW Version' vs 'Program SW-Version'
    squished = "".join(ch for ch in raw if ch.isalnum())
    for k, v in CANON_LABELS.items():
        k_squished = "".join(ch for ch in k if ch.isalnum())
        if squished == k_squished:
            return v

    # fall back to original as-is if unknown
    return text.strip()

def parse_header(df: pd.DataFrame, max_rows: int = 4):
    """
    Parse up to the first `max_rows` rows as 2-column key/value pairs.
    - Column 0: label (string)
    - Column 1: value (string)
    - Stops early if Column 0 == 'Frame' (table header reached).
    Returns: ordered list of (key, value).
    """
    results = []
    if df is None or df.empty:
        return results

    nrows = min(max_rows, df.shape[0])
    for r in range(nrows):
        # Stop if we hit the actual table header row
        try:
            k_raw = str(df.iat[r, 0]).strip()
        except Exception:
            k_raw = ""
        if k_raw and k_raw.lower() == "frame":
            break

        # Pull the value column
        try:
            v_raw = str(df.iat[r, 1]).strip()
        except Exception:
            v_raw = ""

        # Skip truly empty/NaN-ish rows
        if not k_raw or k_raw.lower() == "nan":
            continue
        if not v_raw or v_raw.lower() == "nan":
            # Keep keys without values? For this app, we skip them.
            continue

        key = _normalize_label(k_raw)
        value = v_raw
        results.append((key, value))

    return results