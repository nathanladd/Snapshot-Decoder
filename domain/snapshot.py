from __future__ import annotations  # For forward references in type hints (if needed later, e.g., for chart_cart integration)

import os
import math
from typing import Optional, Dict, List, Tuple
import pandas as pd

from domain.snaptypes import SnapType
from domain.constants import HEADER_LABELS, PID_KEY, UNIT_NORMALIZATION, ENGINE_HOURS_COLUMNS
from file_io.reader_excel import load_xls, load_xlsx


class Snapshot:
    """
    Domain entity representing a loaded and parsed snapshot.
    
    Encapsulates raw and cleaned data, header information, PID metadata,
    snapshot type, and derived values like engine hours.
    """
    
    def __init__(self, path: str):
        self.file_path: str = path
        self.file_name: str = os.path.basename(path)
        self.raw_snapshot: Optional[pd.DataFrame] = None
        self.snapshot: Optional[pd.DataFrame] = None
        self.date_time: Optional[str] = None
        self.header_list: List[Tuple[str, str]] = []
        self.pid_info: Dict[str, Dict[str, str]] = {}
        self.snapshot_type: SnapType = SnapType.EMPTY
        self.hours: float = 0.0
        self.mdp_success_rate: float = 0.0
        
    
    @classmethod
    def load(cls, path: str) -> Snapshot:
        """
        Load and parse a snapshot from the given file path.
        """
        instance = cls(path)
        instance._load_and_parse()
        return instance
    
    def _load_and_parse(self):
        """
        Internal method to load the file and perform all parsing steps.
        """
        # Determine file type and load raw data
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext == ".xlsx":
            self.raw_snapshot = load_xlsx(self.file_path)
        elif ext == ".xls":
            self.raw_snapshot = load_xls(self.file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
        
        if self.raw_snapshot is None or self.raw_snapshot.empty:
            raise ValueError("The workbook loaded but no data table was found.")
        
        # Parse header information
        self.header_list = self.parse_header(self.raw_snapshot, max_rows=5)
        
        # Extract date/time from header
        self.date_time = self.find_date_time()
        print(f"Date/Time: {self.date_time}")

        # Find header row and identify snapshot type
        header_row_idx = self.find_pid_names(self.raw_snapshot)
        self.snapshot_type = self.id_snapshot(self.raw_snapshot, header_row_idx)
        
        # Extract PID descriptions
        self.pid_info = extract_pid_descriptions(self.raw_snapshot, header_row_idx)
        
        # Clean the snapshot
        self.snapshot = scrub_snapshot(self.raw_snapshot, header_row_idx)
        
        # Extract engine hours
        self.hours = self.find_engine_hours()
        
        # Extract MDP success rate
        self.mdp_success_rate = self.calculate_mdp_success()
        
        # Set the unit for SMC_ENGINE_STATE PID if the snapshot is ECU_V1 type
        if self.snapshot_type == SnapType.ECU_V1:
            if "SMC_ENGINE_STATE" in self.pid_info:
                self.pid_info["SMC_ENGINE_STATE"]["Unit"] = "[0]Off   [1]Cranking   [2]Running   [3]Stalling"
        
    def find_engine_hours(self) -> float:
        """
        Find the engine hours in the snapshot by reading specific columns based on snapshot type.
        Gets the value at Frame == 0 and converts from seconds to hours.
        
        Returns:
            Engine hours as float rounded to tenth of an hour, or 0 if not found
        """
        # Get the column name for this snapshot type from constants
        column_name = ENGINE_HOURS_COLUMNS.get(self.snapshot_type)
        if not column_name:
            return 0.0  # No engine hours column defined for this snapshot type
        
        # Check if column exists in the snapshot
        if column_name not in self.snapshot.columns:
            return 0.0
        
        # Check if Frame column exists
        if "Frame" not in self.snapshot.columns:
            return 0.0
        
        # Get the row where Frame == 0
        frame_zero_rows = self.snapshot[self.snapshot["Frame"] == 0]
        if frame_zero_rows.empty:
            return 0.0
        
        # Get the unit from pid_info to determine if conversion is needed
        unit = ""
        if column_name in self.pid_info:
            unit = self.pid_info[column_name].get("Unit", "").lower()
        
        # If unit contains "second", convert from seconds to hours
        if "second" in unit:
            try:
                seconds = float(frame_zero_rows[column_name].iloc[0])
                # Convert seconds to hours and round to tenth of an hour
                hours = round(seconds / 3600, 1)
                return hours
            except (ValueError, IndexError, TypeError):
                return 0.0
        else:
            # Unit is hours or unknown, return the value directly
            try:
                return round(float(frame_zero_rows[column_name].iloc[0]), 1)
            except (ValueError, IndexError, TypeError):
                return 0.0

    def find_date_time(self) -> str:
        """
        Find the date/time value in the header list.
        
        Returns:
            Date/time string if found, empty string otherwise
        """
        for label, value in self.header_list:
            if label == "Date / Time":
                return value
        return ""
        

    def calculate_mdp_success(self) -> float:
        """
        Calculate the MDP_SUCCESS value in the snapshot.
        
        Returns:
            MDP Success as float rounded to hundredth of a percent, or 0 if not found
        """
        # Check if MDP_SUCCESS column exists
        if not ("I_C_Mdp_nb_update_failure_nvv" in self.snapshot.columns and "I_C_Mdp_nb_update_success_nvv" in self.snapshot.columns):
            return 0
        
        # Check if Frame column exists
        if "Frame" not in self.snapshot.columns:
            return 0
        
        # Get the row where Frame == 0
        frame_zero_row = self.snapshot[self.snapshot["Frame"] == 0]
        if frame_zero_row.empty:
            return 0
        
        # Get the MDP_SUCCESS value from Frame == 0
        try:
            mdp_success = int(frame_zero_row["I_C_Mdp_nb_update_success_nvv"].iloc[0])
            mdp_success_rate = mdp_success / (frame_zero_row["I_C_Mdp_nb_update_failure_nvv"].iloc[0] + frame_zero_row["I_C_Mdp_nb_update_success_nvv"].iloc[0])
            return round(mdp_success_rate * 100, 1)

        except (ValueError, IndexError, TypeError):
            return 0

    def _normalize_label(self, text: str) -> str:
        """
        Normalize a label to a canonical display name if recognized.
        Loosened matching: exact, case-insensitive; also allows minor spacing/punctuation differences.
        """
        if not text:
            return ""
        raw = text.strip().lower()
        # quick exact lookup
        if raw in HEADER_LABELS:
            return HEADER_LABELS[raw]

        # light fuzzy: remove punctuation/spaces to catch 'Program SW Version' vs 'Program SW-Version'
        squished = "".join(ch for ch in raw if ch.isalnum())
        for k, v in HEADER_LABELS.items():
            k_squished = "".join(ch for ch in k if ch.isalnum())
            if squished == k_squished:
                return v

        # fall back to original as-is if unknown
        return text.strip()

    def parse_header(self, snapshot: pd.DataFrame, max_rows: int = 5):
        """
        Parse up to the first `max_rows` rows as 2-column label/value pairs.
        - Column 0: label (string)
        - Column 1: value (string)
        - Stops early if Column 0 == 'Frame' (table header reached).
        Returns: ordered list of (label, value).
        """
        results = []
        if snapshot is None or snapshot.empty:
            return results

        # Get the number of rows to parse: the smaller of 'max_rows' or total rows in the snapshot
        nrows = min(max_rows, snapshot.shape[0])
        for r in range(nrows):
            # Stop if we hit the table row containing "frame"
            try:
                label_raw = str(snapshot.iat[r, 0]).strip()
            except Exception:
                label_raw = ""
            if label_raw and label_raw.lower() == "frame":
                break

            # Pull the value column
            try:
                value = str(snapshot.iat[r, 1]).strip()
            except Exception:
                value = ""

            # Skip truly empty/NaN-ish rows
            if not label_raw or label_raw.lower() == "nan":
                continue
            if not value or value.lower() == "nan":
                # Keep labels without values? For this app, we skip them.
                continue

            # Check if "Start Time :" is in the label and split it
            if "Start Time :" in label_raw:
                # Split on "Start Time :" to separate label from value
                parts = label_raw.split("Start Time :", 1)
                if len(parts) == 2 and parts[1].strip():
                    # Use the text after "Start Time :" as the value
                    value = parts[1].strip()
                    # Remove colon and trim spaces from label
                    label_raw = "Start Time".strip()
            
            label = self._normalize_label(label_raw)
            results.append((label, value))

        return results

    def id_snapshot(self, snapshot: pd.DataFrame, header_row_idx: int) -> SnapType:
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

    def find_pid_names(self, snapshot: pd.DataFrame) -> int:
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



def _to_str(cell) -> str:
    """Convert any cell to a cleaned string, treating NaN/None as empty."""
    if cell is None:
        return ""
    if isinstance(cell, float) and math.isnan(cell):
        return ""
    s = str(cell).strip()
    return "" if s.lower() in ("nan", "none") else s

def _within(df: pd.DataFrame, r: int) -> bool:
    """True if r is a valid row index for df."""
    return 0 <= r < len(df)

def extract_pid_descriptions(df: pd.DataFrame, header_row_idx: int, start_col: int = 2) -> Dict[str, Dict[str, str]]:
    """
    HORIZONTAL TABLES ONLY
    Extract the PID description and PID unit of measure for each PID
    """
    
    # Initialize the dictionary to store PID information
    # Dictionary <PID Name, Dictionary<Description, Unit>>
    pid_info: Dict[str, Dict[str, str]] = {}

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
    snapshot = snapshot.apply(pd.to_numeric, errors="coerce")

    # Convert time to datetime
    if "Time" in snapshot.columns:
        if pd.api.types.is_numeric_dtype(snapshot["Time"]):
            snapshot["Time"] = pd.to_timedelta(snapshot["Time"], unit="s")
            snapshot["Time"] = snapshot["Time"].dt.total_seconds()
        else:
            pass  # Leave as is if conversion fails
    return snapshot