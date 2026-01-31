"""
Background snapshot loader with progress updates.

Loads snapshots in a dedicated QThread to keep the UI responsive,
emitting Qt signals at each processing phase.
"""

import os
from typing import Optional

from PySide6.QtCore import QThread, Signal

from domain.snapshot import Snapshot
from domain.snapshot.header_parser import parse_header, find_date_time
from domain.snapshot.type_detector import find_header_row, detect_snapshot_type
from domain.snapshot.pid_extractor import extract_pid_info
from domain.snapshot.data_cleaner import scrub_snapshot, remove_unsupported_pids
from domain.snapshot.time_processor import (
    process_time_column,
    find_engine_hours,
    find_idle_time,
    calculate_mdp_success,
)
from domain.snapshot.value_converter import apply_type_specific_conversions
from domain.snapshot.system_detector import detect_systems
from file_io.reader_excel import load_xls, load_xlsx


class SnapshotLoader(QThread):
    """
    Background thread for loading snapshots with progress updates.
    
    Signals:
        progress: Emitted with (percent, message) during loading
        finished_loading: Emitted with Snapshot object on successful load
        error: Emitted with error message string on failure
    """
    
    # Signals
    progress = Signal(int, str)           # (percent, message)
    finished_loading = Signal(object)     # Snapshot on success
    error = Signal(str)                   # Error message on failure
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation (checked between phases)."""
        self._cancelled = True
    
    def run(self):
        """Execute the snapshot loading pipeline."""
        try:
            snapshot = Snapshot(self.file_path)
            
            # Phase 1: Load raw data
            self.progress.emit(5, "Reading file...")
            snapshot.raw_table = self._load_raw_file()
            if self._cancelled:
                return
            
            if snapshot.raw_table is None or snapshot.raw_table.empty:
                self.error.emit("The workbook loaded but no data table was found.")
                return
            
            # Phase 2: Parse header information
            self.progress.emit(20, "Parsing headers...")
            snapshot.header_list = parse_header(snapshot.raw_table, max_rows=5)
            snapshot.date_time = find_date_time(snapshot.header_list)
            if self._cancelled:
                return
            
            # Phase 3: Find header row and identify snapshot type
            self.progress.emit(35, "Identifying snapshot type...")
            header_row_idx = find_header_row(snapshot.raw_table)
            snapshot.snapshot_type = detect_snapshot_type(snapshot.raw_table, header_row_idx)
            if self._cancelled:
                return
            
            # Phase 4: Extract PID metadata
            self.progress.emit(50, "Extracting PID metadata...")
            snapshot.pid_info = extract_pid_info(snapshot.raw_table, header_row_idx)
            if self._cancelled:
                return
            
            # Phase 5: Clean the snapshot data
            self.progress.emit(65, "Cleaning data...")
            snapshot.snapshot = scrub_snapshot(snapshot.raw_table, header_row_idx, snapshot.pid_info)
            snapshot.snapshot = remove_unsupported_pids(snapshot.snapshot, snapshot.pid_info)
            if self._cancelled:
                return
            
            # Phase 6: Process time column
            self.progress.emit(75, "Processing time data...")
            snapshot.snapshot = process_time_column(snapshot.snapshot)
            if self._cancelled:
                return
            
            # Phase 7: Apply type-specific conversions
            self.progress.emit(80, "Applying conversions...")
            snapshot.snapshot = apply_type_specific_conversions(
                snapshot.snapshot, snapshot.snapshot_type, snapshot.pid_info
            )
            if self._cancelled:
                return
            
            # Phase 8: Extract derived values
            self.progress.emit(90, "Calculating derived values...")
            snapshot.hours = find_engine_hours(
                snapshot.snapshot, snapshot.snapshot_type, snapshot.pid_info
            )
            snapshot.idle_time = find_idle_time(snapshot.snapshot, snapshot.pid_info)
            snapshot.mdp_success_rate = calculate_mdp_success(snapshot.snapshot)
            if self._cancelled:
                return
            
            # Phase 9: Detect engine systems
            self.progress.emit(95, "Detecting systems...")
            systems = detect_systems(snapshot.snapshot)
            snapshot.has_egr = systems.egr
            snapshot.has_doc = systems.doc
            snapshot.has_dpf = systems.dpf
            snapshot.has_scr = systems.scr
            snapshot.has_air_throttle = systems.air_throttle
            snapshot._detected_systems = systems
            
            self.progress.emit(100, "Complete")
            self.finished_loading.emit(snapshot)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _load_raw_file(self):
        """Load raw data from file based on extension."""
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext == ".xlsx":
            return load_xlsx(self.file_path)
        elif ext == ".xls":
            return load_xls(self.file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
