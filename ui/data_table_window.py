import tkinter as tk
from tkinter import ttk
import pandas as pd


class DataTableWindow:
    def __init__(self, parent, snapshot: pd.DataFrame, snapshot_path: str, window_name: str):
        self.parent = parent
        self.snapshot = snapshot
        self.snapshot_path = snapshot_path
        self.window_name = window_name

        self.win = tk.Toplevel(parent)
        self.win.title(f"{window_name}: {snapshot_path}")
        self.win.geometry("1000x600")

        # Style to make headings bold
        style = ttk.Style(self.win)
        style.configure("Treeview.Heading", font=("TkDefaultFont", 9, "bold"))

        container = ttk.Frame(self.win)
        container.pack(fill=tk.BOTH, expand=True)

        # ---- Sanitize column names for Treeview ----
        raw_cols = list(snapshot.columns)
        safe_cols = []
        used = set()
        for i, c in enumerate(raw_cols):
            name = str(c).strip()
            if not name or name.lower() == "nan":
                name = f"col_{i+1}"
            base = name
            k = 1
            while name in used:
                k += 1
                name = f"{base}_{k}"
            used.add(name)
            safe_cols.append(name)

        # Use a display copy with safe column names
        df_display = snapshot.copy()
        df_display.columns = safe_cols

        # Scrollbars
        xscroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL)
        yscroll = ttk.Scrollbar(container, orient=tk.VERTICAL)

        tree = ttk.Treeview(
            container,
            columns=safe_cols,     # must be a list of strings
            show="headings",       # hide the #0 column
            xscrollcommand=xscroll.set,
            yscrollcommand=yscroll.set,
            height=24
        )
        xscroll.config(command=tree.xview)
        yscroll.config(command=tree.yview)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Headings + widths
        for col in safe_cols:
            tree.heading(col, text=col, anchor='center')
            # width heuristic: 150px min, 300px max, based on ~80th percentile of text length
            try:
                w = max(150, min(300, int(df_display[col].astype(str).map(len).quantile(0.8)) * 8))
            except Exception:
                w = 120
                # I disabled stretch to prevent columns from getting slammed
            tree.column(col, width=w, stretch=False, minwidth=w, anchor='center')

        # Insert rows (convert cells to strings; empty for NaN)
        self._iid_to_time = {}
        for i, (_, row) in enumerate(df_display.iterrows()):
            values = [(("" if pd.isna(v) else v)) for v in row.tolist()]
            values = [str(v) for v in values]
            iid = tree.insert("", tk.END, values=values)
            if "Time" in df_display.columns:
                self._iid_to_time[iid] = row.get("Time")

        self._tree = tree

        def _on_close():
            try:
                if self.window_name == "Chart Table":
                    self.parent.chart_table_window = None
            finally:
                self.win.destroy()

        self.win.protocol("WM_DELETE_WINDOW", _on_close)
