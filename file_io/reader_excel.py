import pandas as pd

#Use the opened path to extract Snapshot data
def load_xlsx(path: str) -> pd.DataFrame:
    """Load Excel, find header row containing a PID from the pattern dictionary, set headers,
    and return data starting from Frame == 0. Enforces first two headers as Frame/Time if present.
    """
    # Read raw snapshot so we can pull the header information and scan rows
    return pd.read_excel(path, header=None, engine="calamine")


#Use the opened path to extract Snapshot data
def load_xls(path: str) -> pd.DataFrame:
    """Load Excel, find header row containing a PID from the pattern dictionary, set headers,
    and return data starting from Frame == 0. Enforces first two headers as Frame/Time if present.
    """
    # Read raw snapshot so we can pull the header information and scan rows
    # dirty_snapshot = pd.read_csv(path, sep=",", encoding="utf-16")

    with open(path, "r", encoding="utf-16") as f:
        text = f.read()
    rows = text.split("\n")
    data = [r.split("\t") for r in rows]
    return pd.DataFrame(data)