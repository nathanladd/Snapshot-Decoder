import pandas as pd

# Use the Pandas openpyxl engine to read the Excel file
def load_xlsx(path: str) -> pd.DataFrame:
    '''Read the file as XLSX and return a DataFrame'''
    return pd.read_excel(path, header=None, engine="openpyxl")


# Read the file as UTF-16 and return a DataFrame
def load_xls(path: str) -> pd.DataFrame:
    '''Read the file as UTF-16 and return a DataFrame'''
    with open(path, "r", encoding="utf-16") as f:
        text = f.read()
    rows = text.split("\n")
    data = [r.split("\t") for r in rows]
    return pd.DataFrame(data)