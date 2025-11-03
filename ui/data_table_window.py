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

        # Add progress bar for loading indication
        self.progress_label = ttk.Label(container, text="Preparing to load data...")
        self.progress_label.pack(pady=(10,0))
        self.progress = ttk.Progressbar(container, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X, padx=10, pady=(0,10))
        self.progress['value'] = 0
        self.win.update()  # Force UI update to show progress bar

        # ---- Sanitize column names for tksheet ----
        self.progress_label.config(text="Sanitizing column names...")
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

        self.progress['value'] = 50
        self.progress_label.config(text="Column names sanitized, preparing data...")
        self.win.update()

        # Use a display copy with safe column names
        df_display = snapshot.copy()
        df_display.columns = safe_cols

        # Convert DataFrame to list of lists
        self.progress_label.config(text="Converting data to sheet format...")
        all_data = df_display.astype(str).values.tolist()

        self.progress['value'] = 70
        self.progress_label.config(text="Data converted, creating spreadsheet...")
        self.win.update()

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

        self.progress['value'] = 80
        self.progress_label.config(text="Spreadsheet created, configuring...")
        self.win.update()

        # Enable specific table interactions (selection, resizing, and editing)
        sheet.enable_bindings("single_select", "row_select", "column_select","column_width_resize", "arrowkeys", "right_click_popup_menu", "rc_select", "rc_insert_row", "rc_delete_row", "copy", "cut", "paste", "delete", "undo", "edit_cell")
        # Refresh the sheet to ensure proper display
        sheet.refresh()

        self.progress['value'] = 90
        self.progress_label.config(text="Configuring display settings...")
        self.win.update()

        # Set default column width - users can resize manually
        for i in range(len(safe_cols)):
            sheet.column_width(column=i, width=120)

        self.progress['value'] = 100
        self.progress_label.config(text="Loading complete!")
        self.win.update()

        # Hide the progress bar now that loading is complete
        self.progress.pack_forget()
        self.progress_label.pack_forget()

        def _on_close():
            self.win.destroy()

        self.win.protocol("WM_DELETE_WINDOW", _on_close)
