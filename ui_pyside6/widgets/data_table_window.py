"""
Data table window for PySide6.

Provides a spreadsheet view of snapshot data with search and lazy loading.
"""

import pandas as pd
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QProgressBar, QMessageBox, QApplication,
    QSplitter, QFrame, QAbstractItemView, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QBrush

# Lazy loading constants
INITIAL_ROW_BATCH = 200  # Number of rows to load initially
ROW_LOAD_BATCH = 200     # Number of rows to load when scrolling


class DataPreparationThread(QThread):
    """Background thread for preparing data."""
    data_ready = Signal(list, list)  # data, headers
    error_occurred = Signal(str)
    
    def __init__(self, snapshot: pd.DataFrame):
        super().__init__()
        self.snapshot = snapshot
        self._cancelled = False
    
    def cancel(self):
        """Cancel the preparation."""
        self._cancelled = True
    
    def run(self):
        """Prepare data in background thread."""
        try:
            # Sanitize column names
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

            if self._cancelled:
                return

            # Use a display copy with safe column names
            df_display = self.snapshot.copy()
            df_display.columns = safe_cols

            # Convert DataFrame to list of lists
            all_data = df_display.astype(str).values.tolist()

            if self._cancelled:
                return

            # Emit prepared data
            self.data_ready.emit(all_data, safe_cols)
            
        except Exception as e:
            if not self._cancelled:
                self.error_occurred.emit(str(e))


class DataTableWindow(QMainWindow):
    """Data table window for viewing snapshot data."""
    
    def __init__(self, parent, snapshot: pd.DataFrame, snapshot_path: str, window_name: str):
        super().__init__(parent)
        self.snapshot = snapshot
        self.snapshot_path = snapshot_path
        self.window_name = window_name
        
        # Data prepared by background thread
        self._all_data = None  # Full dataset
        self._headers = None   # Column headers
        self._rows_loaded = 0  # Number of rows currently in table
        self._loading_more = False  # Prevent concurrent loads
        
        # Search state
        self._search_matches = []  # List of (row, col) tuples
        self._header_matches = []  # List of column indices for header matches
        self._current_match_index = -1
        
        # Background thread
        self._prep_thread = None
        
        self._setup_ui()
        self._start_data_preparation()
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle(f"{self.window_name}: {self.snapshot_path}")
        self.setGeometry(100, 100, 1000, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Info frame with stats
        info_frame = QFrame()
        info_frame_layout = QHBoxLayout(info_frame)
        
        self.total_pids_label = QLabel(f"Total PIDs: {len(self.snapshot.columns)}")
        self.total_pids_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        info_frame_layout.addWidget(self.total_pids_label)
        
        self.total_frames_label = QLabel(f"Total Frames: {len(self.snapshot)}")
        self.total_frames_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        info_frame_layout.addWidget(self.total_frames_label)
        
        # Rows loaded indicator and Load More button
        self.rows_loaded_label = QLabel("")
        self.rows_loaded_label.setFont(QFont("Segoe UI", 9))
        info_frame_layout.addWidget(self.rows_loaded_label)
        
        self.load_more_btn = QPushButton("Load More Rows")
        self.load_more_btn.clicked.connect(self._load_more_rows)
        info_frame_layout.addWidget(self.load_more_btn)
        
        self.load_all_btn = QPushButton("Load All")
        self.load_all_btn.clicked.connect(self._load_all_remaining_rows)
        info_frame_layout.addWidget(self.load_all_btn)
        
        info_frame_layout.addStretch()
        layout.addWidget(info_frame)
        
        # Search frame
        search_frame = QFrame()
        search_frame_layout = QHBoxLayout(search_frame)
        
        search_frame_layout.addWidget(QLabel("Search:"))
        
        self.search_entry = QLineEdit()
        self.search_entry.returnPressed.connect(self._do_search)
        search_frame_layout.addWidget(self.search_entry)
        
        self.find_btn = QPushButton("Find")
        self.find_btn.clicked.connect(self._do_search)
        search_frame_layout.addWidget(self.find_btn)
        
        self.prev_btn = QPushButton("▲")
        self.prev_btn.clicked.connect(self._prev_match)
        search_frame_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("▼")
        self.next_btn.clicked.connect(self._next_match)
        search_frame_layout.addWidget(self.next_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_search)
        search_frame_layout.addWidget(clear_btn)
        
        self.search_result_label = QLabel("")
        search_frame_layout.addWidget(self.search_result_label)
        
        search_frame_layout.addStretch()
        layout.addWidget(search_frame)
        
        # Progress bar for loading indication
        self.progress_label = QLabel("Preparing data in background...")
        layout.addWidget(self.progress_label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress)
        
        # Table widget will be created after data is prepared
        self.table_widget = None
    
    def _start_data_preparation(self):
        """Start background data preparation."""
        self._prep_thread = DataPreparationThread(self.snapshot)
        self._prep_thread.data_ready.connect(self._on_data_ready)
        self._prep_thread.error_occurred.connect(self._on_error)
        self._prep_thread.start()
    
    def _on_data_ready(self, data: list, headers: list):
        """Handle prepared data."""
        self._all_data = data
        self._headers = headers
        self._create_table()
    
    def _on_error(self, message: str):
        """Handle preparation error."""
        self.progress_label.setText(f"Error loading data: {message}")
        self.progress_label.setStyleSheet("color: red;")
        self.progress.hide()
    
    def _create_table(self):
        """Create the table widget with initial data."""
        # Hide progress indicators
        self.progress_label.hide()
        self.progress.hide()
        
        # Create table widget
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(min(INITIAL_ROW_BATCH, len(self._all_data)))
        self.table_widget.setColumnCount(len(self._headers))
        self.table_widget.setHorizontalHeaderLabels(self._headers)
        
        # Set selection behavior
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Load initial batch of data
        initial_rows = min(INITIAL_ROW_BATCH, len(self._all_data))
        for row_idx in range(initial_rows):
            for col_idx, value in enumerate(self._all_data[row_idx]):
                item = QTableWidgetItem(str(value))
                self.table_widget.setItem(row_idx, col_idx, item)
        
        self._rows_loaded = initial_rows
        
        # Set column widths
        header = self.table_widget.horizontalHeader()
        for i in range(len(self._headers)):
            header.resizeSection(i, 120)
        
        # Add to layout
        self.centralWidget().layout().addWidget(self.table_widget)
        
        # Update UI
        self._update_rows_loaded_label()
    
    def _update_rows_loaded_label(self):
        """Update the label showing how many rows are loaded."""
        if self._all_data is None:
            return
        
        total = len(self._all_data)
        if self._rows_loaded >= total:
            self.rows_loaded_label.setText("(All rows loaded)")
            self.load_more_btn.setEnabled(False)
            self.load_all_btn.setEnabled(False)
        else:
            self.rows_loaded_label.setText(f"(Showing {self._rows_loaded} of {total} rows)")
            self.load_more_btn.setEnabled(True)
            self.load_all_btn.setEnabled(True)
    
    def _load_more_rows(self):
        """Load the next batch of rows into the table."""
        if self._loading_more or self._all_data is None or self.table_widget is None:
            return
        if self._rows_loaded >= len(self._all_data):
            return
        
        self._loading_more = True
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            total = len(self._all_data)
            start_row = self._rows_loaded
            end_row = min(start_row + ROW_LOAD_BATCH, total)
            
            # Add rows to table
            current_row_count = self.table_widget.rowCount()
            new_rows_needed = end_row - start_row
            self.table_widget.setRowCount(current_row_count + new_rows_needed)
            
            # Fill new rows with data
            for row_offset in range(new_rows_needed):
                row_idx = start_row + row_offset
                for col_idx, value in enumerate(self._all_data[row_idx]):
                    item = QTableWidgetItem(str(value))
                    self.table_widget.setItem(current_row_count + row_offset, col_idx, item)
            
            self._rows_loaded = end_row
            self._update_rows_loaded_label()
            
        finally:
            self._loading_more = False
            QApplication.restoreOverrideCursor()
    
    def _load_all_remaining_rows(self):
        """Load all remaining rows."""
        while self._rows_loaded < len(self._all_data):
            self._load_more_rows()
            QApplication.processEvents()  # Keep UI responsive
    
    def _do_search(self):
        """Search all cells and headers for the search term."""
        if self.table_widget is None:
            return
        
        search_term = self.search_entry.text().strip().lower()
        if not search_term:
            self._clear_search()
            return
        
        # Load all data first if not already loaded
        if self._rows_loaded < len(self._all_data):
            self._load_all_remaining_rows()
        
        # Clear previous highlights
        self._clear_highlights()
        self._search_matches = []
        self._header_matches = []
        self._current_match_index = -1
        
        # Search through headers first
        for col_idx, header in enumerate(self._headers):
            if search_term in str(header).lower():
                self._header_matches.append(col_idx)
        
        # Search through all data
        for row_idx, row in enumerate(self._all_data):
            for col_idx, cell in enumerate(row):
                if search_term in str(cell).lower():
                    self._search_matches.append((row_idx, col_idx))
        
        # Highlight matches and navigate to first
        total_matches = len(self._header_matches) + len(self._search_matches)
        
        if total_matches > 0:
            # Highlight all matches
            self._highlight_all_matches()
            self._current_match_index = 0
            self._go_to_current_match()
            self._update_search_label()
        else:
            self.search_result_label.setText("No matches found")
    
    def _get_total_matches(self):
        """Get total number of matches (headers + cells)."""
        return len(self._header_matches) + len(self._search_matches)
    
    def _next_match(self):
        """Navigate to the next search match."""
        total = self._get_total_matches()
        if total == 0:
            return
        
        # Reset current match color back to yellow
        self._reset_current_match_color()
        
        self._current_match_index = (self._current_match_index + 1) % total
        self._go_to_current_match()
        self._update_search_label()
    
    def _prev_match(self):
        """Navigate to the previous search match."""
        total = self._get_total_matches()
        if total == 0:
            return
        
        # Reset current match color back to yellow
        self._reset_current_match_color()
        
        self._current_match_index = (self._current_match_index - 1) % total
        self._go_to_current_match()
        self._update_search_label()
    
    def _reset_current_match_color(self):
        """Reset the current match color back to yellow."""
        if self.table_widget is None:
            return
        
        # Header matches come first in the index
        if self._current_match_index < len(self._header_matches):
            col_idx = self._header_matches[self._current_match_index]
            first_row_item = self.table_widget.item(0, col_idx)
            if first_row_item:
                first_row_item.setBackground(QColor(255, 255, 200))  # Light yellow
        else:
            # Cell match
            cell_idx = self._current_match_index - len(self._header_matches)
            row_idx, col_idx = self._search_matches[cell_idx]
            if row_idx < self.table_widget.rowCount():
                item = self.table_widget.item(row_idx, col_idx)
                if item:
                    item.setBackground(QColor(255, 255, 200))  # Light yellow
    
    def _go_to_current_match(self):
        """Scroll to and select the current match."""
        total = self._get_total_matches()
        if total == 0 or self._current_match_index < 0 or self.table_widget is None:
            return
        
        # Header matches come first in the index
        if self._current_match_index < len(self._header_matches):
            col_idx = self._header_matches[self._current_match_index]
            # Select header
            self.table_widget.selectColumn(col_idx)
            self.table_widget.scrollToItem(self.table_widget.item(0, col_idx))
        else:
            # Cell match
            cell_idx = self._current_match_index - len(self._header_matches)
            row_idx, col_idx = self._search_matches[cell_idx]
            
            # Ensure the row is loaded
            if row_idx >= self.table_widget.rowCount():
                return
            
            # Select and highlight current match with different color
            item = self.table_widget.item(row_idx, col_idx)
            if item:
                self.table_widget.setCurrentItem(item)
                self.table_widget.scrollToItem(item)
                # Highlight current match with a different color
                item.setBackground(QColor(255, 200, 100))  # Orange
    
    def _update_search_label(self):
        """Update the search result count label."""
        total = self._get_total_matches()
        if total > 0:
            self.search_result_label.setText(f"Match {self._current_match_index + 1} of {total}")
        else:
            self.search_result_label.setText("")
    
    def _clear_search(self):
        """Clear search highlights and reset search state."""
        self._clear_highlights()
        self._search_matches = []
        self._header_matches = []
        self._current_match_index = -1
        self.search_result_label.setText("")
        self.search_entry.clear()
    
    def _clear_highlights(self):
        """Clear all highlighted cells."""
        if self.table_widget is None:
            return
        
        # Clear all cell highlights
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    item.setBackground(QBrush())  # Reset to default
        
        # Clear header highlights by resetting selection
        self.table_widget.clearSelection()
    
    def _highlight_all_matches(self):
        """Highlight all search matches."""
        if self.table_widget is None:
            return
        
        # Highlight header matches
        for col_idx in self._header_matches:
            header_item = self.table_widget.horizontalHeaderItem(col_idx)
            if header_item:
                # Headers don't have background, so we'll highlight the first row
                first_row_item = self.table_widget.item(0, col_idx)
                if first_row_item:
                    first_row_item.setBackground(QColor(255, 255, 200))  # Light yellow
        
        # Highlight cell matches
        for row_idx, col_idx in self._search_matches:
            if row_idx < self.table_widget.rowCount():
                item = self.table_widget.item(row_idx, col_idx)
                if item:
                    item.setBackground(QColor(255, 255, 200))  # Light yellow
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self._prep_thread and self._prep_thread.isRunning():
            self._prep_thread.cancel()
            self._prep_thread.wait(1000)  # Wait up to 1 second
        event.accept()
