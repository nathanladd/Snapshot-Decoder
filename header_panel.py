# header_panel.py
# Simple, dependable 2-column header panel + parser for your Snapshot Reader.

import tkinter as tk
from tkinter import ttk
import pandas as pd

#Dictionary variable
# Standardize the labels found in the header. - labels we expect in row 0..3, col 0, with values in col 1.
CANON_LABELS = {
    "engine model": "Engine Model",
    "ecu map version": "ECU Map Version",
    "program sw version": "Program SW Version",
    "data logging": "Data Logging"
}

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

def parse_simple_header(df: pd.DataFrame, max_rows: int = 4):
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


class SimpleHeaderPanel(ttk.Frame):
    """
    Minimal two-column label panel for showing header key/value pairs.
    Usage:
        panel = SimpleHeaderPanel(parent)
        panel.set_rows([("Engine Model","X"), ("ECU Map Version","Y")])
    """
    

    def __init__(self, master, title=""):
        super().__init__(master)

        # Style to set background color
        style = ttk.Style()
        style.configure("Orange_Background.TFrame", background="#FF9634")

        # Layout: 2 columns (key/value)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        # # Set frame size
        # self.config(width=400, height=130)
        # self.grid_propagate(False)
        # self.configure(style="Orange_Background.TFrame")

        # Fill in Titles and Headings
        self.header_title = ttk.Label(self, text=title, font=("Segoe UI", 11, "bold"), anchor="center")
        self.header_title.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 3))

        #Add a 3rd column to make white space between header and PID info
        self.columnconfigure(2,minsize=30)

        #Add all the bold title informaion to the header
        self.version_title = ttk.Label(self, text="PID Information", font=("Segoe UI", 11, "bold"), anchor="center")
        self.version_title.grid(row=0, column=3, columnspan=2, sticky="nsew", pady=(0, 3))
        self.engine_version = ttk.Label(self, text="Engine Version:", font=("Segoe UI", 9, "bold"))
        self.engine_version.grid(row=1, column=3, sticky="ne", pady=(0, 3))
        self.pids_found = ttk.Label(self, text="PIDs Found:", font=("Segoe UI", 9, "bold"))
        self.pids_found.grid(row=2, column=3, sticky="ne", pady=(0, 3))
        self.frames_found = ttk.Label(self, text="Frames:", font=("Segoe UI", 9, "bold"))
        self.frames_found.grid(row=3, column=3, sticky="ne", pady=(0, 3))

        #Set the minimum size of PID info columns to center the title over the information
        self.columnconfigure(3,minsize=80)
        self.columnconfigure(4,minsize=80)

        self._row_start = 1
        self._rows = []  # track widgets so we can clear

    #Accept PID info and fill the correct header labels
    def set_pid_info(self, snap_type="", pids_found="", frames_found=""):
            '''V1 or V2 engine, number of PIDS, and Frames'''
            st_lbl = ttk.Label(self, text=snap_type, justify="left", anchor="w",)
            st_lbl.grid(row=1, column=4, sticky="w", padx=(0, 3), pady=1)
            pids_lbl = ttk.Label(self, text=pids_found, justify="left", anchor="w",)
            pids_lbl.grid(row=2, column=4, sticky="w", padx=(0, 3), pady=1)
            frames_lbl = ttk.Label(self, text=frames_found, justify="left", anchor="w",)
            frames_lbl.grid(row=3, column=4, sticky="w", padx=(0, 3), pady=1)

    def clear(self):
        for w in self._rows:
            w.destroy()
        self._rows.clear()

    def set_rows(self, pairs):
        """
        pairs: iterable of (key, value)
        """
        self.clear()
        r = self._row_start
        # Show known keys in a friendly order first, then the rest
        priority = ["Engine Model", "ECU Map Version", "Program SW Version", "Data Logging"]
        used = set()

        def add_row(k, v):
            k_lbl = ttk.Label(self, text=f"{k}:", font=("Segoe UI", 9, "bold"))
            v_lbl = ttk.Label(self, text=v, justify="left", anchor="w",)
            k_lbl.grid(row=r_dict["r"], column=0, sticky="ne", padx=(0, 5), pady=1)
            v_lbl.grid(row=r_dict["r"], column=1, sticky="w", pady=1)
            self._rows.extend([k_lbl, v_lbl])
            r_dict["r"] += 1

        r_dict = {"r": r}
        # priority pass
        for want in priority:
            for k, v in pairs:
                if k == want and (k, v) not in used:
                    add_row(k, v)
                    used.add((k, v))
        # remaining
        for k, v in pairs:
            if (k, v) not in used:
                add_row(k, v)
