"""
Background snapshot loader with progress updates.

Loads snapshots in a dedicated QThread to keep the UI responsive,
emitting Qt signals at each processing phase.
"""

import os
import time
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
from domain.snapshot.value_converter import (
    apply_type_specific_conversions,
    convert_temperature_to_us_units,
    convert_pressure_to_us_units,
    convert_millivolts_to_volts,
)
from domain.snapshot.system_detector import detect_systems
from file_io.reader_excel import load_xls, load_xlsx
from infrastructure import log_custody, log_file_loaded, log_file_error, log_phase, log_summary, debug, error as log_error, info


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
    partial_loading = Signal(object)       # Raw snapshot on identification failure
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
        start_time = time.time()
        file_size = 0
        
        try:
            # Phase 1: Load raw data
            self.progress.emit(5, "Reading file...")
            log_phase(1, "Reading File")
            
            # Log loading attempt
            log_custody("LOAD_STARTED", f"File: {self.file_path}")
            debug(f"Starting to load snapshot: {self.file_path}")
            
            # Get file size for logging
            try:
                file_size = os.path.getsize(self.file_path)
                debug(f"File size: {file_size:,} bytes")
            except OSError:
                warning("Could not determine file size")
            
            snapshot = Snapshot(self.file_path)
            snapshot.raw_table = self._load_raw_file()
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 1 - Reading file")
                return
            
            if snapshot.raw_table is None or snapshot.raw_table.empty:
                error_msg = "The workbook loaded but no data table was found."
                log_file_error(self.file_path, error_msg)
                self.error.emit(error_msg)
                return
            
            # Phase 2: Find header row and identify snapshot type
            self.progress.emit(20, "Identifying snapshot type...")
            log_phase(2, "Identifying Snapshot Type")
            
            try:
                header_row_idx = find_header_row(snapshot.raw_table)
                debug(f"Found header row at index: {header_row_idx}")
                
                snapshot.snapshot_type, confidence = detect_snapshot_type(snapshot.raw_table, header_row_idx)
                debug(f"Detected snapshot type: {snapshot.snapshot_type} with {confidence:.1%} confidence")
                
                # Check for minimum 80% confidence
                min_confidence = 0.8
                if confidence < min_confidence:
                    error_msg = f"Snapshot type detection failed: {snapshot.snapshot_type.name} only {confidence:.1%} confidence (minimum {min_confidence:.0%} required)"
                    log_error(error_msg)
                    log_file_error(self.file_path, error_msg)
                    
                    # Enhanced error logging
                    log_error(f"TYPE DETECTION FAILED - Confidence too low:")
                    log_error(f"  File: {self.file_path}")
                    log_error(f"  Detected Type: {snapshot.snapshot_type.name}")
                    log_error(f"  Confidence: {confidence:.1%}")
                    log_error(f"  Required: {min_confidence:.0%}")
                    log_error(f"  Header Row Index: {header_row_idx}")
                    
                    # Log available PIDs for debugging
                    try:
                        header_pids = snapshot.raw_table.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist()
                        log_error(f"  Available PIDs ({len(header_pids)}): {', '.join(header_pids[:10])}{'...' if len(header_pids) > 10 else ''}")
                    except Exception as pid_error:
                        log_error(f"  Could not log header PIDs: {pid_error}")
                    
                    # Load raw data for inspection despite identification failure
                    log_error(f"Loading raw data for inspection despite identification failure")
                    self.progress.emit(100, "Raw data loaded (identification failed)")
                    
                    # Emit partial loading signal instead of error
                    self.partial_loading.emit(snapshot)
                    return
                else:
                    info(f"Type detection passed: {snapshot.snapshot_type.name} with {confidence:.1%} confidence")
                    
            except Exception as e:
                error_msg = f"Snapshot type detection failed with error: {str(e)}"
                log_error(error_msg)
                log_file_error(self.file_path, error_msg)
                
                # Enhanced error logging for exceptions
                log_error(f"TYPE DETECTION ERROR:")
                log_error(f"  File: {self.file_path}")
                log_error(f"  Error: {str(e)}")
                log_error(f"  Error Type: {type(e).__name__}")
                
                self.error.emit(error_msg)
                return
            
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 2 - Identifying snapshot type")
                return
            
            # Phase 3: Parse header information
            self.progress.emit(35, "Parsing headers...")
            log_phase(3, "Parsing Headers")
            snapshot.header_list = parse_header(snapshot.raw_table, max_rows=5)
            snapshot.date_time = find_date_time(snapshot.header_list)
            
            # Log all parsed header information
            if snapshot.header_list:
                info(f"Parsed {len(snapshot.header_list)} header fields:")
                for label, value in snapshot.header_list:
                    info(f"  Header: {label} = {value}")
                log_custody("HEADERS_PARSED", f"Count: {len(snapshot.header_list)} | DateTime: {snapshot.date_time}")
            else:
                info("No header information found")
                warning("HEADERS_PARSED", "Count: 0 | No headers found")
            
            if self._cancelled:
                warning("LOAD_CANCELLED", "Phase 3 - Parsing headers")
                return
            
            # Phase 4: Extract PID metadata
            self.progress.emit(50, "Extracting PID metadata...")
            log_phase(4, "Extracting PID Metadata")
            snapshot.pid_info = extract_pid_info(snapshot.raw_table, header_row_idx)
            debug(f"Extracted {len(snapshot.pid_info)} PIDs")
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 4 - Extracting PID metadata")
                return
            
            # Phase 5: Clean the snapshot data
            self.progress.emit(65, "Cleaning data...")
            log_phase(5, "Cleaning Data")
            snapshot.snapshot = scrub_snapshot(snapshot.raw_table, header_row_idx, snapshot.pid_info)
            snapshot.snapshot = remove_unsupported_pids(snapshot.snapshot, snapshot.pid_info)
            debug(f"Data cleaned, shape: {snapshot.snapshot.shape}")
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 5 - Cleaning data")
                return
            
            # Phase 6: Process time column
            self.progress.emit(75, "Processing time data...")
            log_phase(6, "Processing Time Column")
            snapshot.snapshot = process_time_column(snapshot.snapshot)
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 6 - Processing time data")
                return
            
            # Phase 7: Apply type-specific conversions
            self.progress.emit(80, "Applying conversions...")
            log_phase(7, "Applying Conversions")
            snapshot.snapshot = apply_type_specific_conversions(
                snapshot.snapshot, snapshot.snapshot_type, snapshot.pid_info
            )
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 7 - Applying conversions")
                return
            
            # Phase 7b: Standardize units to US
            self.progress.emit(83, "Standardizing units...")
            log_phase("7b", "Standardizing Units")
            snapshot.snapshot = convert_temperature_to_us_units(snapshot.snapshot, snapshot.pid_info)
            snapshot.snapshot = convert_pressure_to_us_units(snapshot.snapshot, snapshot.pid_info)
            snapshot.snapshot = convert_millivolts_to_volts(snapshot.snapshot, snapshot.pid_info)
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 7b - Standardizing units")
                return
            
            # Phase 8: Extract derived values
            self.progress.emit(90, "Calculating derived values...")
            log_phase(8, "Calculating Derived Values")
            snapshot.hours = find_engine_hours(
                snapshot.snapshot, snapshot.snapshot_type, snapshot.pid_info
            )
            snapshot.idle_time = find_idle_time(snapshot.snapshot, snapshot.pid_info)
            snapshot.mdp_success_rate = calculate_mdp_success(snapshot.snapshot)
            
            # Log derived values calculation
            info(f"Derived values calculated:")
            info(f"  Engine Hours: {snapshot.hours}")
            info(f"  Idle Time: {snapshot.idle_time}")
            info(f"  MDP Success Rate: {snapshot.mdp_success_rate}")
            
            # Log custody event for derived values
            derived_details = f"Hours: {snapshot.hours} | Idle: {snapshot.idle_time} | MDP: {snapshot.mdp_success_rate}"
            log_custody("DERIVED_VALUES_CALCULATED", derived_details)
            
            if self._cancelled:
                log_custody("LOAD_CANCELLED", "Phase 8 - Calculating derived values")
                return
            
            # Phase 9: Detect engine systems
            self.progress.emit(95, "Detecting systems...")
            log_phase(9, "Detecting Engine Systems")
            systems = detect_systems(snapshot.snapshot)
            snapshot.has_egr = systems.egr
            snapshot.has_doc = systems.doc
            snapshot.has_dpf = systems.dpf
            snapshot.has_scr = systems.scr
            snapshot.has_air_throttle = systems.air_throttle
            snapshot.has_mdp = systems.mdp
            snapshot._detected_systems = systems
            debug(f"Detected systems: EGR={systems.egr}, DOC={systems.doc}, DPF={systems.dpf}, SCR={systems.scr}, MDP={systems.mdp}")
            
            # Calculate load time and log success
            load_time = time.time() - start_time
            record_count = len(snapshot.snapshot) if snapshot.snapshot is not None else 0
            
            self.progress.emit(100, "Complete")
            
            # Log chain of custody
            log_file_loaded(
                self.file_path, 
                file_size, 
                str(snapshot.snapshot_type), 
                load_time, 
                record_count
            )
            
            # Summary block
            systems_list = [s for s, v in [
                ("EGR", systems.egr), ("DOC", systems.doc),
                ("DPF", systems.dpf), ("SCR", systems.scr),
                ("MDP", systems.mdp), ("Air Throttle", systems.air_throttle),
            ] if v]
            log_summary([
                f"Snapshot loaded successfully in {load_time:.2f}s",
                f"Type: {snapshot.snapshot_type}",
                f"Records: {record_count:,}",
                f"PIDs: {len(snapshot.pid_info)}",
                f"Systems: {', '.join(systems_list) if systems_list else 'None detected'}",
                f"Engine Hours: {snapshot.hours}",
                f"Idle Time: {snapshot.idle_time}",
                f"MDP Success: {snapshot.mdp_success_rate}",
            ])
            
            self.finished_loading.emit(snapshot)
            
        except Exception as e:
            load_time = time.time() - start_time
            error_msg = str(e)
            log_error(f"Failed to load snapshot after {load_time:.2f}s: {error_msg}")
            log_file_error(self.file_path, error_msg)
            self.error.emit(error_msg)
    
    def _load_raw_file(self):
        """Load raw data from file based on extension."""
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext == ".xlsx":
            return load_xlsx(self.file_path)
        elif ext == ".xls":
            return load_xls(self.file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
