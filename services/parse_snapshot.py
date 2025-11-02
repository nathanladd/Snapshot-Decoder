from domain.snaptypes import SnapType
from domain.constants import PID_KEY, UNIT_NORMALIZATION
import pandas as pd
import math



def id_snapshot(snapshot: pd.DataFrame, header_row_idx: int) -> SnapType:
    '''
    ID the snapshot type based on the header row
    '''
    # Clean and normalize each cell to lowercase strings
    row_values = snapshot.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist()

    # Check if any known header keyword appears in this row
    for pattern, st in PID_KEY.items():
        if any(v == pattern for v in row_values):
            return st
    # if pattern not found, return EMPTY
    return SnapType.EMPTY
      

def find_pid_names(snapshot: pd.DataFrame) -> int:
    '''
    Find the header row
    '''
    header_row_idx = None
    # Scan the first 10 rows
    for i in range(min(len(snapshot), 10)):
        # Clean and normalize each cell to lowercase strings
        row_values = snapshot.iloc[i].astype(str).str.strip().str.lower().tolist()
        #print(f"Row {i}: {row_values}")

        # Check if any known header keyword appears in this row
        for pattern, snap_type in PID_KEY.items():
            if any(v == pattern for v in row_values):
                #print(f"Match found in row {i}")
                return i  # stop once a match is found
        #else:
            # The 'else' on a for-loop runs only if the loop didn't break
            #print(f"No match found in row {i}")

    if header_row_idx is None:
        raise ValueError("[Find Header Row] Couldn't locate header row containing useful information.")


 # ------------------------------------------------------------------------------------------------------------------------
 # ---------------------------------------------- Extract PID Descriptions ------------------------------------------------
 # ------------------------------------------------------------------------------------------------------------------------   

#Helper function for extract_pid_metadata
def _to_str(cell) -> str:
    """Convert any cell to a cleaned string, treating NaN/None as empty."""
    if cell is None:
        return ""
    if isinstance(cell, float) and math.isnan(cell):
        return ""
    s = str(cell).strip()
    return "" if s.lower() in ("nan", "none") else s

#Helper function for extract_pid_metadata
def _within(df: pd.DataFrame, r: int) -> bool:
    """True if r is a valid row index for df."""
    return 0 <= r < len(df)

#Extract the PID description and PID unit of measure for each PID
#Starting at start_col (default: 3rd col), read:
#    - PID name from header_row_idx
#    - Description from row above (header_row_idx - 1)
#    - Unit from row below (header_row_idx + 1)
#    Returns: { PID_name: {"Description": ..., "Unit": ...}, ... }
def extract_pid_descriptions(df: pd.DataFrame, header_row_idx: int, start_col: int = 2) -> dict[str, dict[str, str]]:
    """
    HORIZONTAL TABLES ONLY
    Extract the PID description and PID unit of measure for each PID
    """
    
    # Initialize the dictionary to store PID information
    # Dictionary <PID Name, Dictionary<Description, Unit>>
    pid_info: dict[str, dict[str, str]] = {}

    # Row indices for description and unit (guard if out of bounds)
    desc_row = header_row_idx - 1 if _within(df, header_row_idx - 1) else None
    unit_row = header_row_idx + 1 if _within(df, header_row_idx + 1) else None

    for c in range(start_col, len(df.columns)):
        pid = _to_str(df.iat[header_row_idx, c])
        if not pid:
            continue

        description = _to_str(df.iat[desc_row, c]) if desc_row is not None else ""
        unit = _to_str(df.iat[unit_row, c]) if unit_row is not None else ""

        # Optional: collapse multi-line cells
        description = " ".join(part.strip() for part in description.splitlines() if part.strip())
        unit = " ".join(part.strip() for part in unit.splitlines() if part.strip())

        if unit:
            normalized_unit = UNIT_NORMALIZATION.get(unit.strip().lower())
            if normalized_unit:
                unit = normalized_unit

        pid_info[pid] = {"Description": description, "Unit": unit}

    return pid_info
    

def scrub_snapshot(raw_snapshot: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
    """
    Process the raw snapshot DataFrame:
    - Set column headers from the header row.
    - Normalize column names.
    - Rename first two columns to 'Frame' and 'Time'.
    - Trim to start from Frame == 0 if 'Frame' column exists.
    - Coerce columns to numeric where possible.
    - Convert time to datetime.

    Returns the processed snapshot.
    """
    # Set column header row
    pid_header = raw_snapshot.iloc[header_row_idx].astype(str).str.strip().tolist()
    snapshot = raw_snapshot.iloc[header_row_idx+1:].copy()
    snapshot.columns = pid_header

    # Normalize column names: strip and preserve original case
    snapshot.columns = [str(c).strip() for c in snapshot.columns]

    # Try to ensure first two columns are named exactly Frame and Time
    if len(snapshot.columns) >= 2:
        new_cols = list(snapshot.columns)  # copy all names
        new_cols[0] = "Frame"
        new_cols[1] = "Time"
        snapshot.columns = new_cols

    # Find the start row where Frame == 0 (if Frame exists) and trim before converting time
    if "Frame" in snapshot.columns:
        start_idx = snapshot.index[snapshot["Frame"] == 0]
        if len(start_idx) > 0:
            snapshot = snapshot.loc[start_idx[0]:].reset_index(drop=True)

    # Coerce numerics where possible
    snapshot = snapshot.apply(pd.to_numeric, errors="ignore")

    # Convert time to datetime
    if "Time" in snapshot.columns:
        if pd.api.types.is_numeric_dtype(snapshot["Time"]):
            snapshot["Time"] = pd.to_timedelta(snapshot["Time"], unit="s")
            snapshot["Time"] = snapshot["Time"].dt.total_seconds()
        else:
            # If not numeric, try without unit (assumes string format like "00:00:01")
            try:
                snapshot["Time"] = pd.to_timedelta(snapshot["Time"])
                snapshot["Time"] = snapshot["Time"].dt.total_seconds()
            except ValueError:
                pass  # Leave as is if conversion fails
        



    return snapshot