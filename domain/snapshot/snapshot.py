"""
Main Snapshot class - coordinator for snapshot loading and parsing.

This module provides the primary interface for loading snapshot files,
delegating specific tasks to specialized modules.
"""

from __future__ import annotations

import os
from typing import Optional, Dict, List, Tuple
import pandas as pd

from domain.snaptypes import SnapType
from domain.snapshot.header_parser import parse_header, find_date_time
from domain.snapshot.map_version_decoder import (
    EcuMapInfo,
    decode_map_version,
    find_map_version,
)
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
    convert_temperature_to_us_units,
    convert_pressure_to_us_units,
    convert_millivolts_to_volts,
)
from domain.snapshot.system_detector import detect_systems, DetectedSystems
from file_io.reader_excel import load_xls, load_xlsx


class Snapshot:
    """
    Domain entity representing a loaded and parsed snapshot.
    
    Encapsulates raw and cleaned data, header information, PID metadata,
    snapshot type, and derived values like engine hours.
    """
    
    def __init__(self, path: str):
        self.file_path: str = path
        self.raw_table: Optional[pd.DataFrame] = None
        self.snapshot: Optional[pd.DataFrame] = None

        # Chain of custody parameters
        self.file_name: str = os.path.basename(path)
        self.date_time: Optional[str] = None
        self.hours: float = 0.0

        self.header_list: List[Tuple[str, str]] = []

        # Decoded from the ECU Map Version header (when recognized)
        self.displacement: Optional[str] = None
        self.subtype: Optional[str] = None
        self.horsepower: Optional[str] = None
        self.ecu_map_info: Optional[EcuMapInfo] = None

        self.pid_info: Dict[str, Dict[str, str]] = {}
        self.snapshot_type: SnapType = SnapType.EMPTY
        self.mdp_success_rate: float = 0.0
        self.idle_time: float = 0.0
        
        # Detected engine systems (set during parsing)
        self.has_egr: bool = False
        self.has_doc: bool = False
        self.has_dpf: bool = False
        self.has_scr: bool = False
        # True when has_scr was inferred from temperature sensors on an
        # unverified engine (ECU map version absent/unrecognized).
        self.scr_temp_unverified: bool = False
        self.has_air_throttle: bool = False
        self._detected_systems: Optional[DetectedSystems] = None

    @classmethod
    def load(cls, path: str) -> Snapshot:
        """Load and parse a snapshot from the given file path."""
        instance = cls(path)
        instance._load_and_parse()
        return instance
    
    def _load_and_parse(self) -> None:
        """Internal method to load the file and perform all parsing steps."""
        # (Phase 1) Load raw data based on file type
        self.raw_table = self._load_file()
        
        if self.raw_table is None or self.raw_table.empty:
            raise ValueError("The workbook loaded but no data table was found.")
        
        # (Phase 2) Find header row and identify snapshot type
        header_row_idx = find_header_row(self.raw_table)
        self.snapshot_type, confidence = detect_snapshot_type(self.raw_table, header_row_idx)
        
        # Check for minimum 80% confidence
        min_confidence = 0.8
        if confidence < min_confidence:
            error_msg = f"Snapshot type detection failed: {self.snapshot_type.name} only {confidence:.1%} confidence (minimum {min_confidence:.0%} required)"
            from infrastructure.logging_config import log_error
            log_error(error_msg)
            raise ValueError(error_msg)
        
        # (Phase 3) Parse header information
        self.header_list = parse_header(self.raw_table, max_rows=5)
        self.date_time = find_date_time(self.header_list)
        self._decode_map_version()
        
        # (Phase 4) Extract PID descriptions
        self.pid_info = extract_pid_info(self.raw_table, header_row_idx)
        
        # (Phase 5) Clean the snapshot
        self.snapshot = scrub_snapshot(self.raw_table, header_row_idx, self.pid_info)
        self.snapshot = remove_unsupported_pids(self.snapshot, self.pid_info)
        
        # (Phase 6) Process time column
        self.snapshot = process_time_column(self.snapshot)
        
        # (Phase 7) Standardize units to US
        self.snapshot = convert_temperature_to_us_units(self.snapshot, self.pid_info)
        self.snapshot = convert_pressure_to_us_units(self.snapshot, self.pid_info)
        self.snapshot = convert_millivolts_to_volts(self.snapshot, self.pid_info)
        
        # (Phase 8) Key PIDs
        self.hours = find_engine_hours(self.snapshot, self.snapshot_type, self.pid_info)
        self.idle_time = find_idle_time(self.snapshot, self.pid_info)
        self.mdp_success_rate = calculate_mdp_success(self.snapshot)
        
        # (Phase 9) Detect engine systems
        self._detect_systems()

    def _decode_map_version(self) -> None:
        """Decode the ECU Map Version from the header, if recognized."""
        map_version = find_map_version(self.header_list)
        info = decode_map_version(map_version)
        if info is not None:
            self.ecu_map_info = info
            self.displacement = info.displacement
            self.subtype = info.subtype
            self.horsepower = info.horsepower

    def _detect_systems(self) -> None:
        """Detect which engine systems are present in the snapshot."""
        self._detected_systems = detect_systems(self.snapshot, self.ecu_map_info)
        
        # Set convenience bool attributes
        self.has_egr = self._detected_systems.egr
        self.has_doc = self._detected_systems.doc
        self.has_dpf = self._detected_systems.dpf
        self.has_scr = self._detected_systems.scr
        self.scr_temp_unverified = self._detected_systems.scr_temp_unverified
        self.has_air_throttle = self._detected_systems.air_throttle
        self.has_mdp = self._detected_systems.mdp
    
    def get_detected_systems_summary(self) -> str:
        """Get a human-readable summary of detected systems."""
        from domain.snapshot.system_detector import get_system_summary
        if self._detected_systems:
            return get_system_summary(self._detected_systems)
        return "No systems detected"

    def _load_file(self) -> pd.DataFrame:
        """Load raw data from the file based on extension."""
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext == ".xlsx":
            return load_xlsx(self.file_path)
        elif ext == ".xls":
            return load_xls(self.file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
