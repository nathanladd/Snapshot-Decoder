# io_clean.py
from __future__ import annotations
import os
from typing import Tuple, Optional, List
import pandas as pd

# ---------- File reading ----------

def _looks_like_utf16_tsv(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in {".tsv", ".txt", ""}

def _is_excel(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"}

def read_raw_table(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()

    if ext == ".xls":
        # Warn the user: .xls not supported
        import tkinter.messagebox as messagebox
        messagebox.showerror(
            "Unsupported File Format",
            "Legacy .xls files are not supported by this app.\n\n"
            "Please open the file in Microsoft Excel and re-save it as an .xlsx file, then try again."
        )
        raise ValueError("Unsupported .xls file format")

    elif ext in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return pd.read_excel(path, header=None, engine="openpyxl")

    # Try UTF-16 TSV
    if _looks_like_utf16_tsv(path):
        try:
            return pd.read_csv(path, sep="\t", header=None, encoding="utf-16")
        except Exception:
            pass

    # Fallback: UTF-8 TSV
    return pd.read_csv(path, sep="\t", header=None, encoding="utf-8", errors="ignore")

# ---------- Header construction per your rule ----------

def _ensure_unique_columns(cols: List[str]) -> List[str]:
    counts: dict[str, int] = {}
    out: List[str] = []
    for c in cols:
        c = ("" if c is None else str(c)).strip().upper()
        if c == "":
            c = "COL"
        n = counts.get(c, 0)
        out.append(c if n == 0 else f"{c}.{n+1}")
        counts[c] = n + 1
    return out

def find_pl_battery_header_row(df: pd.DataFrame) -> Optional[int]:
    """
    Search rows starting at index 2 (row 3 in 1-based terms) for a cell that equals
    the exact string 'P_L_Battery_raw' (case-insensitive on purpose).
    Return the row index if found, else None.
    """
    start_idx = 2  # zero-based -> third row
    token_upper = "P_L_BATTERY_RAW"
    for r in range(start_idx, len(df)):
        row_vals = df.iloc[r].astype(str).str.strip()
        if (row_vals.str.upper() == token_upper).any():
            return r
    return None

def build_headers(df: pd.DataFrame, header_row: int) -> List[str]:
    """
    Construct headers per your rule:
    col1='Frame', col2='Time', col3..N = cells from header_row, starting at column index 2.
    Uppercase + ensure uniqueness.
    """
    raw_headers = df.iloc[header_row].tolist()
    out = ["Frame", "Time"]  # Force first two
    rest = [str(x).strip() if pd.notna(x) else "" for x in raw_headers[2:]]
    out.extend(rest)
    return _ensure_unique_columns(out)

def promote_headers_and_trim(df: pd.DataFrame, header_row: int) -> pd.DataFrame:
    """Promote the specified row to be the header using our custom rules and return rows below."""
    cols = build_headers(df, header_row)
    data = df.iloc[header_row + 1 :].copy()

    # Align data width with header width
    if data.shape[1] < len(cols):
        # Pad with empty columns
        for _ in range(len(cols) - data.shape[1]):
            data[data.shape[1]] = pd.NA
    elif data.shape[1] > len(cols):
        data = data.iloc[:, : len(cols)]

    data.columns = cols
    data.reset_index(drop=True, inplace=True)
    return data

# ---------- Trimming, saving, and the pipeline ----------

def subset_from_frame_zero(df: pd.DataFrame) -> pd.DataFrame:
    """
    Use the first column 'FRAME' to find the first row where FRAME == 0, else return as-is.
    """
    if df.columns.size == 0:
        return df
    first_col = df.columns[0]
    if str(first_col).upper() != "FRAME":
        return df
    ser = pd.to_numeric(df[first_col], errors="coerce")
    mask = ser.eq(0)
    if not mask.any():
        return df
    idx = mask.idxmax()
    return df.loc[idx:].reset_index(drop=True)

def autosize_columns_openpyxl(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    from openpyxl.utils import get_column_letter
    ws = writer.sheets[sheet_name]
    for i, col in enumerate(df.columns, start=1):
        width = max(10, len(str(col)) + 2)
        ws.column_dimensions[get_column_letter(i)].width = width

def save_clean_excel(df: pd.DataFrame, source_path: str, sheet_name: str = "Snapshot") -> str:
    base, _ = os.path.splitext(source_path)
    out_path = f"{base}_CLEAN.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        autosize_columns_openpyxl(writer, sheet_name, df)
    return out_path

def clean_engine_data(path: str) -> Tuple[pd.DataFrame, Optional[str], List[str]]:
    """
    High-level cleaning pipeline implementing the custom header rule.
    Returns: (clean_df, saved_path, warnings)
    """
    warnings: List[str] = []

    # Step 1: read raw
    raw = read_raw_table(path)

    # Step 2: find header row containing P_L_Battery_raw (starting from row 3)
    header_row = find_pl_battery_header_row(raw)
    if header_row is None:
        warnings.append("Couldn't find 'P_L_Battery_raw' starting at row 3; using row 0 as header source.")
        header_row = 0

    # Step 3: promote headers (Frame/Time forced + rest from header_row)
    tbl = promote_headers_and_trim(raw, header_row)

    # Step 4: trim from FRAME == 0 using first column
    before_len = len(tbl)
    tbl = subset_from_frame_zero(tbl)
    if len(tbl) == before_len:
        warnings.append("Didn't find FRAME == 0; showing all rows after header.")

    # Step 5: best-effort numeric coercion
    for c in tbl.columns:
        if c == "TIME":
            tbl[c] = pd.to_numeric(tbl[c], errors="ignore")
        elif c == "FRAME":
            tbl[c] = pd.to_numeric(tbl[c], errors="coerce")
        else:
            try:
                tbl[c] = pd.to_numeric(tbl[c].astype(str).str.replace(",", "", regex=False), errors="ignore")
            except Exception:
                pass

    # Step 6: save
    saved_path: Optional[str] = None
    try:
        saved_path = save_clean_excel(tbl, path, sheet_name="Snapshot")
    except Exception as e:
        warnings.append(f"Failed to save clean Excel: {e}")

    return tbl, saved_path, warnings
