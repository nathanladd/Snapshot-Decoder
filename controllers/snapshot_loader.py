"""
Background snapshot loader with progress updates.

Loads snapshots in a dedicated QThread to keep the UI responsive,
emitting Qt signals at each processing phase.
"""

import os
import time

from PySide6.QtCore import QThread, Signal

from domain.snapshot import Snapshot
from domain.snapshot.snapshot import SnapshotTypeDetectionError
from domain.snapshot.map_version_decoder import find_map_version
from infrastructure import log_chain_of_custody, log_file_loaded, log_file_error, log_phase, log_summary, log_debug, log_error, log_info, log_warning


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
        """Execute the snapshot loading pipeline by driving Snapshot's phase
        methods one at a time, so this thread and Snapshot.load() share one
        implementation of the actual parsing logic."""
        start_time = time.time()
        file_size = 0

        try:
            # Phase 1: Load raw data
            self.progress.emit(5, "Reading file...")
            log_phase(1, "Reading File")

            # Log loading attempt
            log_chain_of_custody("LOAD_STARTED", f"File: {self.file_path}")
            log_debug(f"Starting to load snapshot: {self.file_path}")

            # Get file size for logging
            try:
                file_size = os.path.getsize(self.file_path)
                log_debug(f"File size: {file_size:,} bytes")
            except OSError:
                log_warning("Could not determine file size")

            snapshot = Snapshot(self.file_path)
            try:
                snapshot._phase1_load_file()
            except ValueError as e:
                if self._cancelled:
                    log_chain_of_custody("LOAD_CANCELLED", "Phase 1 - Reading file")
                    return
                error_msg = str(e)
                log_file_error(self.file_path, error_msg)
                self.error.emit(error_msg)
                return

            if self._cancelled:
                log_chain_of_custody("LOAD_CANCELLED", "Phase 1 - Reading file")
                return

            # Phase 2: Find header row and identify snapshot type
            self.progress.emit(20, "Identifying snapshot type...")
            log_phase(2, "Identifying Snapshot Type")

            try:
                header_row_idx, confidence = snapshot._phase2_detect_type()
                log_debug(f"Found header row at index: {header_row_idx}")
                log_debug(f"Detected snapshot type: {snapshot.snapshot_type} with {confidence:.1%} confidence")
                log_info(f"Type detection passed: {snapshot.snapshot_type.name} with {confidence:.1%} confidence")

            except SnapshotTypeDetectionError as e:
                error_msg = str(e)
                log_error(error_msg)
                log_file_error(self.file_path, error_msg)

                # Enhanced error logging
                log_error(f"TYPE DETECTION FAILED - Confidence too low:")
                log_error(f"  File: {self.file_path}")
                log_error(f"  Detected Type: {snapshot.snapshot_type.name}")
                log_error(f"  Confidence: {e.confidence:.1%}")
                log_error(f"  Required: {e.min_confidence:.0%}")
                log_error(f"  Header Row Index: {e.header_row_idx}")

                # Log available PIDs for log_debugging
                try:
                    header_pids = snapshot.raw_table.iloc[e.header_row_idx].astype(str).str.strip().str.lower().tolist()
                    log_error(f"  Available PIDs ({len(header_pids)}): {', '.join(header_pids[:10])}{'...' if len(header_pids) > 10 else ''}")
                except Exception as pid_error:
                    log_error(f"  Could not log header PIDs: {pid_error}")

                # Load raw data for inspection despite identification failure
                log_error(f"Loading raw data for inspection despite identification failure")
                self.progress.emit(100, "Raw data loaded (identification failed)")

                # Emit partial loading signal instead of error
                self.partial_loading.emit(snapshot)
                return

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
                log_chain_of_custody("LOAD_CANCELLED", "Phase 2 - Identifying snapshot type")
                return

            # Phase 3: Parse header information
            self.progress.emit(35, "Parsing headers...")
            log_phase(3, "Parsing Headers")
            snapshot._phase3_parse_header()

            # Log all parsed header information
            if snapshot.header_list:
                log_info(f"Parsed {len(snapshot.header_list)} header fields:")
                for label, value in snapshot.header_list:
                    log_info(f"  Header: {label} = {value}")
            else:
                log_info("No header information found")
                log_warning("HEADERS_PARSED", "Count: 0 | No headers found")

            # Log the decoded ECU Map Version (decoding itself happened in phase3)
            if snapshot.ecu_map_info is not None:
                map_info = snapshot.ecu_map_info
                log_info(
                    f"Decoded ECU Map Version '{map_info.map_version}': "
                    f"{map_info.engine_version} {map_info.displacement} "
                    f"{map_info.subtype}, HP setting {map_info.horsepower}"
                )
                if not map_info.subtype_recognized:
                    log_warning(f"Unknown subtype code '{map_info.subtype_code}' in ECU Map Version '{map_info.map_version}'")
            else:
                map_version = find_map_version(snapshot.header_list)
                if map_version:
                    log_warning(f"Map Version '{map_version}' did not match known Bobcat format")
                else:
                    log_debug("No ECU Map Version found in header")


            if self._cancelled:
                log_warning("LOAD_CANCELLED", "Phase 3 - Parsing headers")
                return

            # Phase 4: Extract PID metadata
            self.progress.emit(50, "Extracting PIDs...")
            log_phase(4, "Extracting PIDs")
            snapshot._phase4_extract_pids(header_row_idx)
            log_info(f"Successfully extracted PID names, descriptions, and units for {len(snapshot.pid_info)} PIDs")
            log_debug(f"Extracted {len(snapshot.pid_info)} PIDs")
            if self._cancelled:
                log_chain_of_custody("LOAD_CANCELLED", "Phase 4 - Extracting PID metadata")
                return

            # Phase 5: Clean the snapshot data
            self.progress.emit(65, "Cleaning data...")
            log_phase(5, "Cleaning Data")

            log_debug("  Setting column headers from header row")
            log_debug("  Normalizing column names")
            log_debug("  Ensuring Frame and Time columns")
            log_debug("  Converting Frame to numeric and trimming to Frame == 0")
            snapshot._phase5_scrub(header_row_idx)
            log_debug(f"  Scrubbed snapshot: {snapshot.snapshot.shape[0]} rows × {snapshot.snapshot.shape[1]} columns")

            pre_remove_cols = snapshot.snapshot.shape[1]
            log_debug("  Scanning for 'Not supported' PIDs")
            snapshot._phase5_remove_unsupported()
            removed_count = pre_remove_cols - snapshot.snapshot.shape[1]
            log_debug(f"  Removed {removed_count} unsupported PID column(s)")

            log_info(f"Successfully cleaned snapshot data: {snapshot.snapshot.shape[0]} rows × {snapshot.snapshot.shape[1]} columns")
            if self._cancelled:
                log_chain_of_custody("LOAD_CANCELLED", "Phase 5 - Cleaning data")
                return

            # Phase 6: Process time column
            self.progress.emit(75, "Processing time data...")
            log_phase(6, "Processing Time Column")

            has_time_column = "Time" in snapshot.snapshot.columns
            if has_time_column:
                log_debug("  Converting Time column to numeric format")
                log_debug("  Converting Time column to timedelta format")
                log_debug("  Extracting total seconds from timedelta")
            snapshot._phase6_process_time()
            if has_time_column:
                log_info("Successfully processed time column: converted to seconds format")
            else:
                log_info("No Time column found - skipping time processing")

            if self._cancelled:
                log_chain_of_custody("LOAD_CANCELLED", "Phase 6 - Processing time data")
                return

            # Phase 7: Standardize units to US
            self.progress.emit(80, "Standardizing units...")
            log_phase(7, "Converting to Freedom Units")
            snapshot._phase7_convert_units()
            if self._cancelled:
                log_chain_of_custody("LOAD_CANCELLED", "Phase 7 - Standardizing units")
                return

            # Phase 8: Extract derived values
            self.progress.emit(90, "Extracting key PIDs...")
            log_phase(8, "Key PIDs")

            # Check if idle time PID exists before calling find_idle_time
            idle_time_column = "EUD_Engine_idle_time_nvv"
            if idle_time_column not in snapshot.snapshot.columns:
                log_warning(f"Idle time PID '{idle_time_column}' not found - setting to 0.0")

            # Debug logging for MDP calculation
            success_col = "I_C_Mdp_nb_update_success_nvv"
            failure_col = "I_C_Mdp_nb_update_failure_nvv"
            if success_col in snapshot.snapshot.columns and failure_col in snapshot.snapshot.columns:
                if "Frame" in snapshot.snapshot.columns:
                    frame_zero_row = snapshot.snapshot[snapshot.snapshot["Frame"] == 0]
                    if not frame_zero_row.empty:
                        try:
                            mdp_success = int(frame_zero_row[success_col].iloc[0])
                            mdp_failure = int(frame_zero_row[failure_col].iloc[0])
                            log_debug(f"  MDP calculation: Success={mdp_success}, Failure={mdp_failure}, Total={mdp_success + mdp_failure}")
                        except (ValueError, IndexError, TypeError):
                            log_warning("  MDP calculation: Could not parse success/failure values")
                    else:
                        log_warning("  MDP calculation: No Frame==0 row found")
                else:
                    log_warning("  MDP calculation: No Frame column found")
            else:
                log_warning("  MDP calculation: Success/failure columns not found")

            snapshot._phase8_key_pids()

            # Log key PIDs extraction
            log_info(f"Key PIDs extracted:")
            log_info(f"  Engine Hours: {snapshot.hours}")
            log_info(f"  Idle Time: {snapshot.idle_time}")
            log_info(f"  MDP Success Rate: {snapshot.mdp_success_rate}")

            if self._cancelled:
                log_chain_of_custody("LOAD_CANCELLED", "Phase 8 - Extracting key PIDs")
                return

            # Phase 9: Detect engine systems
            self.progress.emit(95, "Detecting systems...")
            log_phase(9, "Detecting Engine Systems")
            snapshot._phase9_detect_systems()
            systems = snapshot._detected_systems
            log_debug(f"Detected systems: EGR={systems.egr}, DOC={systems.doc}, DPF={systems.dpf}, SCR={systems.scr}, MDP={systems.mdp}")

            # Calculate load time and log success
            load_time = time.time() - start_time
            record_count = len(snapshot.snapshot) if snapshot.snapshot is not None else 0
            
            self.progress.emit(100, "Complete")
            
            # Summary block (log_debug level)
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
            
            # Log chain of custody
            log_file_loaded(
                self.file_path, 
                file_size, 
                str(snapshot.snapshot_type), 
                load_time, 
                record_count
            )

            self.finished_loading.emit(snapshot)
            
        except Exception as e:
            load_time = time.time() - start_time
            error_msg = str(e)
            log_error(f"Failed to load snapshot after {load_time:.2f}s: {error_msg}")
            log_file_error(self.file_path, error_msg)
            
            # Emit partial snapshot for raw data inspection if raw_table was loaded
            try:
                if snapshot.raw_table is not None and not snapshot.raw_table.empty:
                    log_info("Raw data available for inspection despite load failure")
                    self.partial_loading.emit(snapshot)
            except NameError:
                pass
            
            self.error.emit(error_msg)
