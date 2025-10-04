"""
Snapshot Reader — Column Selector & Combo Chart (Tkinter)
--------------------------------------------------------
Adds a UI panel that lists all column headers from the loaded dataset and lets
users choose one or more series for a combo *line* chart with dual y-axes.

Key bits:
- File ▶ Open loads an .xlsx and auto-detects the header row using the project rule:
  • Col 1 must be "Frame" and col 2 "Time".
  • Starting around row 3, find the row that contains "P_L_Battery_raw" and
    set that row as the header for the whole table.
  • Start the data where Frame == 0.
- Left panel shows all columns in a searchable, multi-select list.
- Buttons add selections to Primary or Secondary axis buckets (you can add multiple).
- Plot ▶ Combo Line Chart draws all Primary on left axis and Secondary on right axis.
- Embeds Matplotlib figure inside Tkinter.

Requirements (install first):
  pip install pandas matplotlib openpyxl

Note on old .xls files:
  xlrd >= 2.0 dropped support for .xls. This app will politely instruct users to
  open the .xls in Excel and “Save As” .xlsx, then try again.
"""

from __future__ import annotations
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional

import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Class to pull Snapshot header information - if it exists
from header_panel import SimpleHeaderPanel, parse_simple_header

APP_TITLE = "Snapshot Reader"

class SnapshotReaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        #self.geometry("1200x720")
        self.state("zoomed")

        # State
        self.df: Optional[pd.DataFrame] = None
        self.primary_series: List[str] = []
        self.secondary_series: List[str] = []

        # Axis limits state
        self.primary_min = tk.StringVar()
        self.primary_max = tk.StringVar()
        self.secondary_min = tk.StringVar()
        self.secondary_max = tk.StringVar()

        self.primary_ymin = tk.StringVar(value="")
        self.primary_ymax = tk.StringVar(value="")
        self.secondary_ymin = tk.StringVar(value="")
        self.secondary_ymax = tk.StringVar(value="")
        self.primary_auto = tk.BooleanVar(value=True)
        self.secondary_auto = tk.BooleanVar(value=True)

        # Build UI
        self._build_menu()
        self._build_layout()          # uses the variables above
        self._build_plot_area()       # may call _toggle_* which also needs them
        self._update_controls_state(enabled=False)

    # ---------------------- UI Construction ----------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open…", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Data Table…", command=self.open_data_table)
        menubar.add_cascade(label="View", menu=view_menu)

        plot_menu = tk.Menu(menubar, tearoff=0)
        plot_menu.add_command(label="Combo Line Chart", command=self.plot_combo_chart)
        menubar.add_cascade(label="Plot", menu=plot_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About", "Snapshot Reader — Column Selector\nBuild combo line charts from your engine data."))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_layout(self):
        root = ttk.Frame(self)
        root.pack(fill=tk.BOTH, expand=True)

      

        # Snapshot Header Information
        self.header_panel = SimpleHeaderPanel(root, title="Snapshot Header")
        self.header_panel.pack(fill="x", padx=8, pady=8)

        # Left: column pickers
        left = ttk.Frame(root, padding=5)
        left.pack(side=tk.LEFT, fill=tk.Y) 

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)         

        

        ttk.Label(left, text="Search PIDs", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        # Search box
        self.search_var = tk.StringVar()
        search = ttk.Entry(left, textvariable=self.search_var)
        search.pack(fill=tk.X, pady=(4, 8))
        search.bind("<KeyRelease>", lambda e: self._filter_columns())

        # All columns listbox (multi-select)
        self.columns_list = tk.Listbox(left, selectmode=tk.EXTENDED, exportselection=False, height=22, width=40)
        self.columns_list.pack(fill=tk.Y)

        # Buttons to add to primary/secondary
        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=8)
        ttk.Button(btns, text="➕ Add to Primary", command=lambda: self._add_selected(target="primary")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))
        ttk.Button(btns, text="➕ Add to Secondary", command=lambda: self._add_selected(target="secondary")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4,0))

        # Buckets display
        buckets = ttk.Frame(left)
        buckets.pack(fill=tk.BOTH, expand=False)

        # Primary frame with min/max
        primary_frame = ttk.Labelframe(buckets, text="Primary axis (left)")
        primary_frame.pack(fill=tk.BOTH, expand=False, pady=(4,6))
        self.primary_list = tk.Listbox(primary_frame, height=6, exportselection=False)
        self.primary_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pf_controls = ttk.Frame(primary_frame)
        pf_controls.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(pf_controls, text="▲", width=3, command=lambda: self._move_in_list(self.primary_list, -1)).pack(pady=2)
        ttk.Button(pf_controls, text="▼", width=3, command=lambda: self._move_in_list(self.primary_list, +1)).pack(pady=2)
        ttk.Button(pf_controls, text="🗑", width=3, command=lambda: self._remove_selected_from("primary")).pack(pady=2)

        '''  I'm not sure about these min/max boxes in the primary axis frame
        # Axis min/max inputs
        lims = ttk.Frame(primary_frame)
        lims.pack(fill=tk.X, pady=(4,0))
        ttk.Label(lims, text="Min").pack(side=tk.LEFT)
        ttk.Entry(lims, textvariable=self.primary_min, width=6).pack(side=tk.LEFT, padx=(2,10))
        ttk.Label(lims, text="Max").pack(side=tk.LEFT)
        ttk.Entry(lims, textvariable=self.primary_max, width=6).pack(side=tk.LEFT)
        '''

        # Secondary frame with min/max
        secondary_frame = ttk.Labelframe(buckets, text="Secondary axis (right)")
        secondary_frame.pack(fill=tk.BOTH, expand=False)
        self.secondary_list = tk.Listbox(secondary_frame, height=6, exportselection=False)
        self.secondary_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sf_btns = ttk.Frame(secondary_frame)
        sf_btns.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(sf_btns, text="▲", width=3, command=lambda: self._move_in_list(self.secondary_list, -1)).pack(pady=2)
        ttk.Button(sf_btns, text="▼", width=3, command=lambda: self._move_in_list(self.secondary_list, +1)).pack(pady=2)
        ttk.Button(sf_btns, text="🗑", width=3, command=lambda: self._remove_selected_from("secondary")).pack(pady=2)

        # Axis controls
        axis = ttk.Labelframe(left, text="Axis ranges (optional)")
        axis.pack(fill=tk.X, pady=(8,6))

        # Primary axis controls
        p_row = ttk.Frame(axis)
        p_row.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(p_row, text="Primary auto", variable=self.primary_auto, command=self._toggle_primary_inputs).pack(side=tk.LEFT)
        ttk.Label(p_row, text="min").pack(side=tk.LEFT, padx=(8,2))
        self.primary_min_entry = ttk.Entry(p_row, width=8, textvariable=self.primary_ymin)
        self.primary_min_entry.pack(side=tk.LEFT)
        ttk.Label(p_row, text="max").pack(side=tk.LEFT, padx=(8,2))
        self.primary_max_entry = ttk.Entry(p_row, width=8, textvariable=self.primary_ymax)
        self.primary_max_entry.pack(side=tk.LEFT)

        # Secondary axis controls
        s_row = ttk.Frame(axis)
        s_row.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(s_row, text="Secondary auto", variable=self.secondary_auto, command=self._toggle_secondary_inputs).pack(side=tk.LEFT)
        ttk.Label(s_row, text="min").pack(side=tk.LEFT, padx=(8,2))
        self.secondary_min_entry = ttk.Entry(s_row, width=8, textvariable=self.secondary_ymin)
        self.secondary_min_entry.pack(side=tk.LEFT)
        ttk.Label(s_row, text="max").pack(side=tk.LEFT, padx=(8,2))
        self.secondary_max_entry = ttk.Entry(s_row, width=8, textvariable=self.secondary_ymax)
        self.secondary_max_entry.pack(side=tk.LEFT)

        # Plot button
        ttk.Button(left, text="Plot Combo Line Chart", command=self.plot_combo_chart).pack(fill=tk.X, pady=(6,0))

        # Right: figure area
        self.right = ttk.Frame(root, padding=10)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",              # left-align text
            relief="sunken",         # classic status bar look
            padding=(8, 2)
        )
        self.status_bar.pack(side="bottom", fill="x")
    

    def set_status(self, text: str):
        """Update the status bar text and keep the UI snappy."""
        self.status_var.set(text)
        # Force a quick redraw so the message appears immediately
        self.status_bar.update_idletasks()

    def _build_plot_area(self):
        # Create an empty figure placeholder
        self.figure = Figure(figsize=(7,5), dpi=100)
        self.ax_left = self.figure.add_subplot(111)
        self.ax_right = self.ax_left.twinx()
        self.ax_left.set_title("Combo Line Chart")
        self.ax_left.set_xlabel("Index / Time")
        self.ax_left.set_ylabel("Primary")
        self.ax_right.set_ylabel("Secondary")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.right)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

         # Initialize input toggle states after widgets exist
        try:
            self._toggle_primary_inputs()
            self._toggle_secondary_inputs()
        except Exception:
            pass

 

    # ---------------------- Data Loading ----------------------
    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open Engine Data (.xlsx)",
            filetypes=[("Modern Excel", "*.xlsx"), ("Legacy Excel", "*.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext == ".xls":
            messagebox.showwarning(
                "Some Bobcat Engine Analyzer Files Not Supported",
                "Bobcat Engine Analyzer doesn't even really generate legit .xls files.\n\n" \
                "This app can't convert whatever those files are into proper .xlsx files.\n\n" \
                "Open the file in Excel and use its Save As command to convert this file to a proper .xlsx, then try again.")
            return
        try:
            df = self._load_engine_data(path)
        except Exception as e:
            messagebox.showerror("Load failed", f"Couldn't load file.\n\n{e}")
            return

        if df is None or df.empty:
            messagebox.showerror("No data", "The workbook loaded but no data table was found.")
            return

        self.df = df
        self._update_controls_state(enabled=True)
        #Update the status bar with file information
        self.set_status(f"Loaded {len(self.df)} Frames of {len(self.df.columns)} PIDs from file: {os.path.basename(path)}")
        self._populate_columns_list()


    def _load_engine_data(self, path: str) -> pd.DataFrame:
        """Load Excel, find header row containing 'P_L_Battery_raw', set headers,
        and return data starting from Frame == 0. Enforces first two headers as Frame/Time if present.
        """
        # Read raw with no header so we can scan rows
        #raw = pd.read_excel(path, header=None, engine="openpyxl")
        raw = pd.read_excel(path, header=None, engine="calamine")  # works for .xls and .xlsx - More modern and faster than openxl

        # Pull any header information from teh Snapshot if it exists
        header_pairs = parse_simple_header(raw, max_rows=4)

        # If nothing found, show a gentle placeholder
        if header_pairs:
            self.header_panel.set_rows(header_pairs)
        else:
            self.header_panel.set_rows([("Header", "No header info present")])

        # Find header row: somewhere at/after row index 2 (3rd row to humans)
        header_row_idx = None
        for i in range(min(len(raw), 200)):  # scan first 200 rows for safety
            row_values = raw.iloc[i].astype(str).str.strip().str.lower().tolist()
            if any(v == "p_l_battery_raw" for v in row_values):
                header_row_idx = i
                break
        if header_row_idx is None:
            raise ValueError("Couldn't locate header row containing 'P_L_Battery_raw'.")

        # Set header row
        header = raw.iloc[header_row_idx].astype(str).str.strip().tolist()
        df = raw.iloc[header_row_idx+1:].copy()
        df.columns = header

        # Normalize column names: strip and preserve original case
        df.columns = [str(c).strip() for c in df.columns]


        # Try to ensure first two columns are named exactly Frame and Time
        # I had to copy the entire list of column names into a list, change the firts two column names
        # then reassign the names to the data frame - all because the 'NaN' 
        
        if len(df.columns) >= 2:
            new_cols = list(df.columns)  # copy all names
            new_cols[0] = "Frame"
            new_cols[1] = "Time"
            df.columns = new_cols

        # Coerce numerics where possible
        df = df.apply(pd.to_numeric, errors="ignore")

        # Find the start row where Frame == 0 (if Frame exists)
        if "Frame" in df.columns:
            start_idx = df.index[df["Frame"] == 0]
            if len(start_idx) > 0:
                df = df.loc[start_idx[0]:].reset_index(drop=True)

        return df.reset_index(drop=True)

    # ---------------------- Column List Logic ----------------------
    def _populate_columns_list(self):
        self.columns_list.delete(0, tk.END)
        if self.df is None:
            return
        for col in self.df.columns:
            self.columns_list.insert(tk.END, col)

    def _filter_columns(self):
        term = self.search_var.get().strip().lower()
        self.columns_list.delete(0, tk.END)
        if self.df is None:
            return
        cols = [c for c in self.df.columns if term in c.lower()]
        for c in cols:
            self.columns_list.insert(tk.END, c)

    def _add_selected(self, target: str):
        if self.df is None:
            return
        sel = [self.columns_list.get(i) for i in self.columns_list.curselection()]
        if not sel:
            return
        # Prevent duplicates and avoid placing Time or Frame on y-axes (they can still be used on x later)
        filtered = [s for s in sel if s not in ("Frame", "Time")]
        if not filtered:
            messagebox.showinfo("Heads up", "Select one or more PID columns (not Frame/Time).")
            return

        if target == "primary":
            for s in filtered:
                if s not in self.primary_series:
                    self.primary_series.append(s)
                    self.primary_list.insert(tk.END, s)
        else:
            for s in filtered:
                if s not in self.secondary_series:
                    self.secondary_series.append(s)
                    self.secondary_list.insert(tk.END, s)

    def _move_in_list(self, listbox: tk.Listbox, delta: int):
        idxs = list(listbox.curselection())
        if not idxs:
            return
        for idx in idxs:
            new_idx = max(0, min(listbox.size()-1, idx + delta))
            if new_idx == idx:
                continue
            text = listbox.get(idx)
            listbox.delete(idx)
            listbox.insert(new_idx, text)
            listbox.selection_set(new_idx)

        # Mirror to backing lists
        if listbox is self.primary_list:
            self.primary_series = list(listbox.get(0, tk.END))
        else:
            self.secondary_series = list(listbox.get(0, tk.END))

    def _remove_selected_from(self, which: str):
        lb = self.primary_list if which == "primary" else self.secondary_list
        sel = list(lb.curselection())
        if not sel:
            return
        for idx in reversed(sel):
            lb.delete(idx)
        if which == "primary":
            self.primary_series = list(lb.get(0, tk.END))
        else:
            self.secondary_series = list(lb.get(0, tk.END))

    def _update_controls_state(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        for w in (self.columns_list, self.primary_list, self.secondary_list):
            w.configure(state=state)

    def _toggle_primary_inputs(self):
        st = tk.DISABLED if self.primary_auto.get() else tk.NORMAL
        self.primary_min_entry.configure(state=st)
        self.primary_max_entry.configure(state=st)

    def _toggle_secondary_inputs(self):
        st = tk.DISABLED if self.secondary_auto.get() else tk.NORMAL
        self.secondary_min_entry.configure(state=st)
        self.secondary_max_entry.configure(state=st)

    def _parse_limit(self, s: str):
        s = (s or "").strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    # ---------------------- Plotting ----------------------
    def plot_combo_chart(self):
        if self.df is None:
            messagebox.showinfo("No data", "Open a data file first.")
            return
        if not self.primary_series and not self.secondary_series:
            messagebox.showinfo("Select columns", "Add at least one series to Primary or Secondary axis.")
            return

        df = self.df.copy()

        # Choose X: prefer Time if numeric, else Frame, else index
        x_key = None
        if "Time" in df.columns and pd.api.types.is_numeric_dtype(df["Time"]):
            x_key = "Time"
        elif "Frame" in df.columns and pd.api.types.is_numeric_dtype(df["Frame"]):
            x_key = "Frame"

        self.ax_left.clear()
        self.ax_right.clear()

        # Plot primary series
        if self.primary_series:
            for s in self.primary_series:
                if s in df.columns:
                    y = pd.to_numeric(df[s], errors="coerce")
                    if x_key:
                        self.ax_left.plot(df[x_key], y, label=s)
                    else:
                        self.ax_left.plot(y.index, y, label=s)
            self.ax_left.set_ylabel("Primary")
            self.ax_left.legend(loc="upper left")

        # Plot secondary series
        if self.secondary_series:
            for s in self.secondary_series:
                if s in df.columns:
                    y = pd.to_numeric(df[s], errors="coerce")
                    if x_key:
                        self.ax_right.plot(df[x_key], y, label=s, linestyle='--')
                    else:
                        self.ax_right.plot(y.index, y, label=s, linestyle='--')
            self.ax_right.set_ylabel("Secondary")
            self.ax_right.legend(loc="upper right")

        # Apply axis limits if user entered them
        try:
            if self.primary_min.get():
                self.ax_left.set_ylim(bottom=float(self.primary_min.get()))
            if self.primary_max.get():
                self.ax_left.set_ylim(top=float(self.primary_max.get()))
        except ValueError:
            pass
        try:
            if self.secondary_min.get():
                self.ax_right.set_ylim(bottom=float(self.secondary_min.get()))
            if self.secondary_max.get():
                self.ax_right.set_ylim(top=float(self.secondary_max.get()))
        except ValueError:
            pass

        # Labels and grid
        self.ax_left.set_title("Combo Line Chart")
        self.ax_left.set_xlabel(x_key if x_key else "Index")
        self.ax_left.grid(True, linestyle=":", linewidth=0.6)

        # Apply axis limits if provided
        if not self.primary_auto.get():
            ymin = self._parse_limit(self.primary_ymin.get())
            ymax = self._parse_limit(self.primary_ymax.get())
            if ymin is not None or ymax is not None:
                self.ax_left.set_ylim(bottom=ymin if ymin is not None else None,
                              top=ymax if ymax is not None else None)

        if not self.secondary_auto.get():
            ymin = self._parse_limit(self.secondary_ymin.get())
            ymax = self._parse_limit(self.secondary_ymax.get())
            if ymin is not None or ymax is not None:
                self.ax_right.set_ylim(bottom=ymin if ymin is not None else None,
                               top=ymax if ymax is not None else None)

        self.figure.tight_layout()
        self.canvas.draw_idle()

# Build a new window with a clean data table

    def open_data_table(self):
        if self.df is None or self.df.empty:
            messagebox.showinfo("No data", "Open a file first so I can show the cleaned table.")
            return

        # Reuse an existing table window if it's open
        if hasattr(self, "_table_win") and self._table_win and tk.Toplevel.winfo_exists(self._table_win):
            try:
                self._table_win.lift()
                self._table_win.focus_force()
            except Exception:
                pass
            return

        win = tk.Toplevel(self)
        self._table_win = win
        win.title("Validation — Cleaned Data Table")
        win.geometry("1000x600")

        container = ttk.Frame(win)
        container.pack(fill=tk.BOTH, expand=True)

        # ---- Sanitize column names for Treeview ----
        raw_cols = list(self.df.columns)
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
        df_display = self.df.copy()
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
            tree.heading(col, text=col)
            # width heuristic: 80px min, 300px max, based on ~80th percentile of text length
            try:
                w = max(80, min(300, int(df_display[col].astype(str).map(len).quantile(0.8)) * 8))
            except Exception:
                w = 120
            tree.column(col, width=w, stretch=True, anchor=tk.W)

        # Insert rows (convert cells to strings; empty for NaN)
        for _, row in df_display.iterrows():
            values = [(("" if pd.isna(v) else v)) for v in row.tolist()]
            values = [str(v) for v in values]
            tree.insert("", tk.END, values=values)

        def _on_close():
            try:
                self._table_win = None
            finally:
                win.destroy()
        win.protocol("WM_DELETE_WINDOW", _on_close)



def main():
    app = SnapshotReaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()