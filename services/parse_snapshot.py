from domain.snaptypes import SnapType
from domain.constants import PID_KEY
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
      

def find_header_row(snapshot: pd.DataFrame) -> int:
    '''
    Find the header row
    '''
    header_row_idx = None
    # Scan the first 10 rows
    for i in range(min(len(snapshot), 10)):
        # Clean and normalize each cell to lowercase strings
        row_values = snapshot.iloc[i].astype(str).str.strip().str.lower().tolist()
        print(f"Row {i}: {row_values}")

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

        pid_info[pid] = {"Description": description, "Unit": unit}

    return pid_info
    