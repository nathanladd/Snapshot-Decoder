import io
import pandas as pd

# Use the Pandas openpyxl engine to read the Excel file
def load_xlsx(path: str) -> pd.DataFrame:
    '''Read the file as XLSX and return a DataFrame'''
    return pd.read_excel(path, header=None, engine="openpyxl")


# Read the file as UTF-16 tab-delimited text using pandas' C parser
def load_xls(path: str) -> pd.DataFrame:
    '''Read the file as UTF-16 tab-delimited text and return a DataFrame.

    Snapshot exports have ragged row widths (short metadata rows up top,
    then a wide fixed-width PID table), so the column count can't be
    inferred from the first row like a normal CSV. We scan once for the
    widest row and pass that count in explicitly so the C parser pads
    short rows instead of raising a "tokenizing" error.
    '''
    with open(path, "r", encoding="utf-16") as f:
        text = f.read()
    max_cols = max(line.count("\t") for line in text.split("\n")) + 1
    return pd.read_csv(
        io.StringIO(text),
        sep="\t",
        header=None,
        names=range(max_cols),
        dtype=str,
        keep_default_na=False,
        skip_blank_lines=False,
    )


# Original pure-Python implementation, kept for cases where the exact
# manual-split behavior is wanted (e.g. a trailing blank line in the file
# becomes an extra all-empty row here, whereas load_xls drops it).
def load_xls_legacy(path: str) -> pd.DataFrame:
    '''Read the file as UTF-16 and return a DataFrame (slow, manual parse)'''
    with open(path, "r", encoding="utf-16") as f:
        text = f.read()
    rows = text.split("\n")
    data = [r.split("\t") for r in rows]
    return pd.DataFrame(data)