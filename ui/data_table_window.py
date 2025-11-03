import tkinter as tk
from tkinter import ttk
import pandas as pd
import tksheet


class DataTableWindow:
    def __init__(self, parent, snapshot: pd.DataFrame, snapshot_path: str, window_name: str):
        self.parent = parent
        self.snapshot = snapshot
        self.snapshot_path = snapshot_path
        self.window_name = window_name

        self.win = tk.Toplevel(parent)
        self.win.title(f"{window_name}: {snapshot_path}")
        self.win.geometry("1000x600")

        container = ttk.Frame(self.win)
        container.pack(fill=tk.BOTH, expand=True)

        # ---- Sanitize column names for tksheet ----
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

        # Convert DataFrame to list of lists
        all_data = df_display.values.tolist()

        # Create tksheet table widget with all data (tksheet handles virtual scrolling internally)
        sheet = tksheet.Sheet(
            container,
            data=all_data,  # Load all data - tksheet handles virtual display
            headers=safe_cols,
            height=24,
            width=None,
            show_row_index=True,
            show_header=True,
            show_top_left=True,
            set_all_heights_and_widths=True
        )
        sheet.pack(fill=tk.BOTH, expand=True)

        # Enable specific table interactions (selection, resizing) but not editing
        sheet.enable_bindings("column_width_resize", "column_select", "row_select", "cell_select", "drag_select")

        # Refresh the sheet to ensure proper display
        sheet.refresh()

        # Set default column width - users can resize manually
        for i in range(len(safe_cols)):
            sheet.column_width(column=i, width=120)

        def _on_close():
            self.win.destroy()

        self.win.protocol("WM_DELETE_WINDOW", _on_close)
