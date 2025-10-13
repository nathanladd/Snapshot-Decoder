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
from typing import List, Optional, Dict, Callable, Tuple

import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from enum import Enum, auto

# Class to manage Snapshot header information
from header_panel import SimpleHeaderPanel, parse_simple_header

APP_TITLE = "Snapshot Reader"
#Built this enumeration as a class to allow for the tuple and override the string type
#Enumeration to hold the type desription of the snapshot as a global variable
class SnapType(Enum):
    UNKNOWN = ("UNKNOWN", "Unknown Snapshot Type")
    ECU_V1 = ("ECU_V1", "Bobcat V1 Engine (Delphi ECU)")
    DCU_V1 = ("DCU_V1", "Bobcat V1 Engine SCR System (Bosch DCU)")
    EUD_V1 = ("EUD_V1", "Bobcat V1 Engine Use Data")
    ECU_V2 = ("ECU_V2", "Bobcat V2 Engine (Bosch ECU)")
    EUD_V2 = ("EUD_V2", "Bobcat V2 Engine Use Data")

    def __init__(self, type: str, description: str):
        # Initialize the enumeration with a tuple - type of snap and plain word description for labels
        self.type =type
        self.description = description

    def __str__(self):
        #Overrides the string type - when I call the string of this enumeration, I'll get the description from teh tuple
        return self.description




class SnapshotReaderApp(tk.Tk):

    #__init__ is a special built-in method name in Python. 
    # When you create (or “instantiate”) an object from a class, 
    # Python automatically calls this method. 
    # It’s where you set up the initial state of the object — 
    # like its variables, default values, 
    # or anything else that needs to happen right when it’s born.

    def __init__(self):
        # super().__init__() says: “Run whatever setup the parent class 
        # normally does before I do my own stuff.” 
        # It’s like calling your parent’s __init__ before adding 
        # your own custom initialization steps.
        super().__init__()
        
        self._set_window_title()
        self.state("zoomed")

        # State
        self.snapshot: Optional[pd.DataFrame] = None
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
    def _set_window_title(self, file_path=None):
        '''Update the window title
        If a Snapshot is open, include its name and path'''
        if file_path:
            self.title(f"{APP_TITLE} : {file_path}")
        else:
            self.title(APP_TITLE)
   
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
        self.header_frame = SimpleHeaderPanel(root, title="Snapshot Header Information")
        self.header_frame.pack(anchor="nw", padx=4, pady=4)

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
        tk.Button(left, text="Plot Selected PIDs", font=("Segoe UI", 11, "bold"), command=self.plot_combo_chart).pack(fill=tk.X, pady=(6,0))

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
            df = self._load_snapshot_data(path)
        except Exception as e:
            messagebox.showerror("Load failed", f"Couldn't load file.\n\n{e}")
            return

        if df is None or df.empty:
            messagebox.showerror("No data", "The workbook loaded but no data table was found.")
            return

        self.snapshot = df
        self._update_controls_state(enabled=True)
        
        #Update main window title
        self._set_window_title(file_path=os.path.basename(path))

        #Update header frame PID information
        self.header_frame.set_pid_info(pids_found=len(self.snapshot.columns), frames_found=len(self.snapshot))
        
        #Update the status bar with file information
        self.set_status(f"Loaded {len(self.snapshot)} Frames of {len(self.snapshot.columns)} PIDs from file: {os.path.basename(path)}")
        self._populate_columns_list()


    def _load_snapshot_data(self, path: str) -> pd.DataFrame:
        """Load Excel, find header row containing 'P_L_Battery_raw', set headers,
        and return data starting from Frame == 0. Enforces first two headers as Frame/Time if present.
        """
        # Read raw snapshot so we can pull the header information and scan rows
        dirty_snapshot = pd.read_excel(path, header=None, engine="calamine")

        # Pull any header information from the Snapshot if it exists
        header_info = parse_simple_header(dirty_snapshot, max_rows=4)

        # If nothing found, show a gentle placeholder
        if header_info:
            self.header_frame.set_rows(header_info)
        else:
            self.header_frame.set_rows([("Header", "No header info present")])

        # Find header row: somewhere at/after row index 2 (3rd row to humans)
        header_row_idx = None
        for i in range(min(len(dirty_snapshot), 10)):  # scan first 10 rows for safety
            row_values = dirty_snapshot.iloc[i].astype(str).str.strip().str.lower().tolist()
            if any(v == "p_l_battery_raw" for v in row_values):
                header_row_idx = i

                break
        if header_row_idx is None:
            raise ValueError("Couldn't locate header row containing 'P_L_Battery_raw'.")

        # Set header row
        pid_header = dirty_snapshot.iloc[header_row_idx].astype(str).str.strip().tolist()
        clean_snapshot = dirty_snapshot.iloc[header_row_idx+1:].copy()
        clean_snapshot.columns = pid_header

        # Normalize column names: strip and preserve original case
        clean_snapshot.columns = [str(c).strip() for c in clean_snapshot.columns]


        # Try to ensure first two columns are named exactly Frame and Time
        # I had to copy the entire list of column names into a list, change the firts two column names
        # then reassign the names to the data frame - all because the 'NaN' 
        
        if len(clean_snapshot.columns) >= 2:
            new_cols = list(clean_snapshot.columns)  # copy all names
            new_cols[0] = "Frame"
            new_cols[1] = "Time"
            clean_snapshot.columns = new_cols

        # Coerce numerics where possible
        clean_snapshot = clean_snapshot.apply(pd.to_numeric, errors="ignore")

        # Find the start row where Frame == 0 (if Frame exists)
        if "Frame" in clean_snapshot.columns:
            start_idx = clean_snapshot.index[clean_snapshot["Frame"] == 0]
            if len(start_idx) > 0:
                clean_snapshot = clean_snapshot.loc[start_idx[0]:].reset_index(drop=True)

        return clean_snapshot.reset_index(drop=True)


    # ---------------------- Column List Logic ----------------------
    def _populate_columns_list(self):
        self.columns_list.delete(0, tk.END)
        if self.snapshot is None:
            return
        for col in self.snapshot.columns:
            self.columns_list.insert(tk.END, col)

    def _filter_columns(self):
        term = self.search_var.get().strip().lower()
        self.columns_list.delete(0, tk.END)
        if self.snapshot is None:
            return
        cols = [c for c in self.snapshot.columns if term in c.lower()]
        for c in cols:
            self.columns_list.insert(tk.END, c)

    def _add_selected(self, target: str):
        if self.snapshot is None:
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
        if self.snapshot is None:
            messagebox.showinfo("No data", "Open a data file first.")
            return
        if not self.primary_series and not self.secondary_series:
            messagebox.showinfo("Select columns", "Add at least one series to Primary or Secondary axis.")
            return

        df = self.snapshot.copy()

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
        if self.snapshot is None or self.snapshot.empty:
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
        raw_cols = list(self.snapshot.columns)
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
        df_display = self.snapshot.copy()
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