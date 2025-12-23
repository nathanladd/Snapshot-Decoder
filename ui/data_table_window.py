import tkinter as tk
from tkinter import ttk
import pandas as pd
import tksheet
import threading

# Lazy loading constants
INITIAL_ROW_BATCH = 200  # Number of rows to load initially
ROW_LOAD_BATCH = 200     # Number of rows to load when scrolling


class DataTableWindow:
    def __init__(self, parent, snapshot: pd.DataFrame, snapshot_path: str, window_name: str):
        self.parent = parent
        self.snapshot = snapshot
        self.snapshot_path = snapshot_path
        self.window_name = window_name
        
        # Data prepared by background thread
        self._prepared_data = None
        self._prepared_cols = None
        self._loading_cancelled = False
        
        # Lazy loading state
        self._all_data = None  # Full dataset
        self._rows_loaded = 0  # Number of rows currently in sheet
        self._loading_more = False  # Prevent concurrent loads
        
        # Search state
        self._search_matches = []  # List of (row, col) tuples
        self._header_matches = []  # List of column indices for header matches
        self._current_match_index = -1

        self.win = tk.Toplevel(parent)
        self.win.title(f"{window_name}: {snapshot_path}")
        self.win.geometry("1000x600")

        self.container = ttk.Frame(self.win)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Info frame with stats
        info_frame = ttk.Frame(self.container)
        info_frame.pack(fill=tk.X, pady=(5, 0), padx=10)
        
        ttk.Label(info_frame, text=f"Total PIDs: {len(snapshot.columns)}", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(info_frame, text=f"Total Frames: {len(snapshot)}", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 20))
        
        # Rows loaded indicator and Load More button
        self.rows_loaded_label = ttk.Label(info_frame, text="", font=("Segoe UI", 9))
        self.rows_loaded_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.load_more_btn = ttk.Button(info_frame, text="Load More Rows", command=self._load_more_rows)
        self.load_more_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.load_all_btn = ttk.Button(info_frame, text="Load All", command=self._load_all_remaining_rows)
        self.load_all_btn.pack(side=tk.LEFT)
        
        # Search frame
        search_frame = ttk.Frame(self.container)
        search_frame.pack(fill=tk.X, pady=(5, 0), padx=10)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.search_entry.bind("<Return>", lambda e: self._do_search())
        
        ttk.Button(search_frame, text="Find", command=self._do_search, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="▲", command=self._prev_match, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="▼", command=self._next_match, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="Clear", command=self._clear_search, width=6).pack(side=tk.LEFT, padx=2)
        
        self.search_result_label = ttk.Label(search_frame, text="")
        self.search_result_label.pack(side=tk.LEFT, padx=(10, 0))

        # Add progress bar for loading indication
        self.progress_label = ttk.Label(self.container, text="Preparing data in background...")
        self.progress_label.pack(pady=(10,0))
        self.progress = ttk.Progressbar(self.container, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=(0,10))
        self.progress.start(10)  # Start indeterminate animation

        def _on_close():
            self._loading_cancelled = True
            self.win.destroy()

        self.win.protocol("WM_DELETE_WINDOW", _on_close)
        
        # Start background thread for data preparation
        self._thread = threading.Thread(target=self._prepare_data_background, daemon=True)
        self._thread.start()

    def _prepare_data_background(self):
        """Prepare data in background thread (no GUI operations here)."""
        try:
            # Sanitize column names for tksheet
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

            if self._loading_cancelled:
                return

            # Use a display copy with safe column names
            df_display = self.snapshot.copy()
            df_display.columns = safe_cols

            # Convert DataFrame to list of lists (this is often the slow part)
            all_data = df_display.astype(str).values.tolist()

            if self._loading_cancelled:
                return

            # Store prepared data
            self._prepared_data = all_data
            self._prepared_cols = safe_cols

            # Schedule GUI creation on main thread
            self.win.after(0, self._create_sheet_on_main_thread)
            
        except Exception as e:
            if not self._loading_cancelled:
                self.win.after(0, lambda: self._show_error(str(e)))

    def _create_sheet_on_main_thread(self):
        """Create the tksheet widget on the main thread."""
        if self._loading_cancelled or self._prepared_data is None:
            return

        # Update progress label
        self.progress.stop()
        self.progress_label.config(text="Creating spreadsheet...")
        self.progress.config(mode='determinate', maximum=100)
        self.progress['value'] = 50
        self.win.update_idletasks()

        # Store full data for lazy loading
        self._all_data = self._prepared_data
        total_rows = len(self._all_data)
        
        # Load only initial batch of rows
        initial_rows = min(INITIAL_ROW_BATCH, total_rows)
        initial_data = self._all_data[:initial_rows]
        self._rows_loaded = initial_rows

        # Create tksheet table widget with initial batch only
        self.sheet = tksheet.Sheet(
            self.container,
            data=initial_data,
            headers=self._prepared_cols,
            height=24,
            width=None,
            show_row_index=True,
            show_header=True,
            show_top_left=True,
            set_all_heights_and_widths=True
        )
        self.sheet.pack(fill=tk.BOTH, expand=True)

        self.progress['value'] = 70
        self.progress_label.config(text="Configuring spreadsheet...")
        self.win.update_idletasks()

        # Enable specific table interactions (selection, resizing, and editing)
        self.sheet.enable_bindings("single_select", "row_select", "column_select","column_width_resize", "arrowkeys", "right_click_popup_menu", "rc_select", "rc_insert_row", "rc_delete_row", "copy", "cut", "paste", "delete", "undo", "edit_cell")
        
        self.progress['value'] = 85
        self.win.update_idletasks()

        # Set default column width - users can resize manually
        for i in range(len(self._prepared_cols)):
            self.sheet.column_width(column=i, width=120)

        # Refresh the sheet to ensure proper display
        self.sheet.refresh()

        self.progress['value'] = 100
        self.progress_label.config(text="Loading complete!")
        self.win.update_idletasks()

        # Hide the progress bar now that loading is complete
        self.progress.pack_forget()
        self.progress_label.pack_forget()
        
        # Update rows loaded label and button visibility
        self._update_rows_loaded_label()
        
        # Clear prepared data reference (but keep _all_data for lazy loading)
        self._prepared_data = None
        self._prepared_cols = None

    def _show_error(self, message: str):
        """Show error message if data preparation fails."""
        self.progress.stop()
        self.progress.pack_forget()
        self.progress_label.config(text=f"Error loading data: {message}")
        self.progress_label.config(foreground="red")

    def _update_rows_loaded_label(self):
        """Update the label showing how many rows are loaded."""
        if self._all_data is None:
            return
        total = len(self._all_data)
        if self._rows_loaded >= total:
            self.rows_loaded_label.config(text="(All rows loaded)")
            self.load_more_btn.config(state="disabled")
            self.load_all_btn.config(state="disabled")
        else:
            self.rows_loaded_label.config(text=f"(Showing {self._rows_loaded} of {total} rows)")
            self.load_more_btn.config(state="normal")
            self.load_all_btn.config(state="normal")

    def _load_more_rows(self):
        """Load the next batch of rows into the sheet."""
        if self._loading_more or self._all_data is None:
            return
        if self._rows_loaded >= len(self._all_data):
            return
        
        self._loading_more = True
        
        try:
            total = len(self._all_data)
            start_row = self._rows_loaded
            end_row = min(start_row + ROW_LOAD_BATCH, total)
            
            # Get the new rows to add
            new_rows = self._all_data[start_row:end_row]
            
            # Append rows to sheet
            for row in new_rows:
                self.sheet.insert_row(row)
            
            self._rows_loaded = end_row
            self._update_rows_loaded_label()
            self.sheet.refresh()
            
        finally:
            self._loading_more = False
    
    def _load_all_remaining_rows(self):
        """Load all remaining rows (used before search)."""
        if self._all_data is None:
            return
        while self._rows_loaded < len(self._all_data):
            self._load_more_rows()

    def _do_search(self):
        """Search all cells and headers for the search term and highlight matches."""
        if not hasattr(self, 'sheet'):
            return
            
        search_term = self.search_var.get().strip().lower()
        if not search_term:
            self._clear_search()
            return
        
        # Clear previous highlights
        self.sheet.dehighlight_all()
        self._search_matches = []
        self._header_matches = []  # Track header matches separately
        self._current_match_index = -1
        
        # Search through headers first
        headers = self.sheet.headers()
        for col_idx, header in enumerate(headers):
            if search_term in str(header).lower():
                self._header_matches.append(col_idx)
        
        # Search through loaded data only
        data = self.sheet.get_sheet_data()
        for row_idx, row in enumerate(data):
            for col_idx, cell in enumerate(row):
                if search_term in str(cell).lower():
                    self._search_matches.append((row_idx, col_idx))
        
        # Highlight all matches
        total_matches = len(self._header_matches) + len(self._search_matches)
        
        if total_matches > 0:
            # Highlight header matches
            for col_idx in self._header_matches:
                self.sheet.highlight_cells(column=col_idx, canvas="header", bg="yellow")
            
            # Highlight cell matches
            for row_idx, col_idx in self._search_matches:
                self.sheet.highlight_cells(row=row_idx, column=col_idx, bg="yellow")
            
            # Go to first match
            self._current_match_index = 0
            self._go_to_current_match()
            self._update_search_label()
        else:
            self.search_result_label.config(text="No matches found")
        
        self.sheet.refresh()

    def _get_total_matches(self):
        """Get total number of matches (headers + cells)."""
        return len(self._header_matches) + len(self._search_matches)

    def _next_match(self):
        """Navigate to the next search match."""
        total = self._get_total_matches()
        if total == 0:
            return
        self._current_match_index = (self._current_match_index + 1) % total
        self._go_to_current_match()
        self._update_search_label()

    def _prev_match(self):
        """Navigate to the previous search match."""
        total = self._get_total_matches()
        if total == 0:
            return
        self._current_match_index = (self._current_match_index - 1) % total
        self._go_to_current_match()
        self._update_search_label()

    def _go_to_current_match(self):
        """Scroll to and select the current match."""
        total = self._get_total_matches()
        if total == 0 or self._current_match_index < 0:
            return
        
        # Header matches come first in the index
        if self._current_match_index < len(self._header_matches):
            col_idx = self._header_matches[self._current_match_index]
            self.sheet.see(row=0, column=col_idx)
            self.sheet.select_cell(row=0, column=col_idx)
        else:
            # Cell match
            cell_idx = self._current_match_index - len(self._header_matches)
            row_idx, col_idx = self._search_matches[cell_idx]
            self.sheet.see(row=row_idx, column=col_idx)
            self.sheet.select_cell(row=row_idx, column=col_idx)

    def _update_search_label(self):
        """Update the search result count label."""
        total = self._get_total_matches()
        if total > 0:
            self.search_result_label.config(
                text=f"Match {self._current_match_index + 1} of {total}"
            )
        else:
            self.search_result_label.config(text="")

    def _clear_search(self):
        """Clear search highlights and reset search state."""
        if hasattr(self, 'sheet'):
            self.sheet.dehighlight_all()
            self.sheet.refresh()
        self._search_matches = []
        self._header_matches = []
        self._current_match_index = -1
        self.search_result_label.config(text="")
