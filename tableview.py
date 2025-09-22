# ------------------------------------------------
# file: tableview.py
# ------------------------------------------------
import tkinter as tk
from tkinter import ttk
import pandas as pd

class DataTable(ttk.Frame):
    """A minimal DataFrame viewer using Tkinter's Treeview widget.
    It supports vertical/horizontal scrolling and populates rows lazily for moderate-sized tables.
    """
    def __init__(self, master, dataframe: pd.DataFrame, max_rows: int = 5000):
        super().__init__(master)
        self.dataframe = dataframe
        self.max_rows = max_rows

        # Create Treeview with columns from DataFrame
        columns = list(map(str, self.dataframe.columns))
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        # Attach scrollbars
        yscroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        # Make frame expandable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Configure column headings and widths
        for col in columns:
            # Set a modest width based on header length
            width = max(80, len(col) * 10)
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        self._populate_rows()

    def _populate_rows(self):
        # Insert up to max_rows rows for performance
        rows_to_insert = min(len(self.dataframe), self.max_rows)
        for i in range(rows_to_insert):
            # Use .iloc to safely extract values as Python scalars
            row_values = []
            for j in range(self.dataframe.shape[1]):
                val = self.dataframe.iloc[i, j]
                # Convert lists/Series/numpy arrays to string so Treeview can display
                if isinstance(val, (list, tuple)):
                    val = ", ".join(map(str, val))
                row_values.append(val)
            self.tree.insert("", "end", values=row_values)