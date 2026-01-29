"""
Unit tests for snapshot package modules.

Tests the individual modules that make up the refactored snapshot package.
"""

import pytest
import pandas as pd
import math

from domain.snapshot.header_parser import parse_header, find_date_time, _normalize_label
from domain.snapshot.type_detector import find_header_row, detect_snapshot_type
from domain.snapshot.pid_extractor import extract_pid_info, _to_str
from domain.snapshot.data_cleaner import scrub_snapshot, remove_unsupported_pids
from domain.snapshot.time_processor import (
    process_time_column,
    find_engine_hours,
    find_idle_time,
    calculate_mdp_success,
)
from domain.snaptypes import SnapType
from domain.constants import SNAPSHOT_TYPE_PIDS


class TestHeaderParser:
    """Tests for header_parser module."""

    def test_parse_header_basic(self):
        """Test parsing basic header rows."""
        df = pd.DataFrame({
            0: ["File Name:", "Date / Time:", "Frame"],
            1: ["test.xlsx", "2024-01-01", "0"],
        })
        
        result = parse_header(df, max_rows=5)
        
        assert len(result) == 2
        assert ("File Name", "test.xlsx") in result
        assert ("Date / Time", "2024-01-01") in result

    def test_parse_header_stops_at_frame(self):
        """Test that parsing stops when Frame row is reached."""
        df = pd.DataFrame({
            0: ["Header1", "Frame", "Data"],
            1: ["Value1", "0", "100"],
        })
        
        result = parse_header(df, max_rows=5)
        
        assert len(result) == 1
        assert result[0] == ("Header1", "Value1")

    def test_parse_header_colon_in_label(self):
        """Test parsing when label contains colon with value."""
        df = pd.DataFrame({
            0: ["Program SW Version: 1.2.3", "Frame"],
            1: ["nan", "0"],
        })
        
        result = parse_header(df, max_rows=5)
        
        assert len(result) == 1
        assert result[0][0] == "Program SW Version"
        assert result[0][1] == "1.2.3"

    def test_find_date_time(self):
        """Test finding date/time from header list."""
        header_list = [
            ("File Name", "test.xlsx"),
            ("Date / Time", "2024-01-15 10:30:00"),
        ]
        
        result = find_date_time(header_list)
        assert result == "2024-01-15 10:30:00"

    def test_find_date_time_not_found(self):
        """Test when date/time is not in header list."""
        header_list = [("File Name", "test.xlsx")]
        
        result = find_date_time(header_list)
        assert result == ""

    def test_normalize_label(self):
        """Test label normalization."""
        assert _normalize_label("program sw version") == "Program SW Version"
        assert _normalize_label("file name") == "File Name"
        assert _normalize_label("Unknown Label") == "Unknown Label"


class TestTypeDetector:
    """Tests for type_detector module."""

    def test_find_header_row(self):
        """Test finding the header row index."""
        df = pd.DataFrame({
            0: ["Header Info", "Description", "Frame", "0"],
            1: ["Value", "Desc", "Time", "0.0"],
            2: ["", "", "smc_engine_state", "1"],
        })
        
        result = find_header_row(df)
        assert result == 2  # Row with "smc_engine_state"

    def test_find_header_row_not_found(self):
        """Test error when header row not found."""
        df = pd.DataFrame({
            0: ["No", "Valid", "Headers"],
            1: ["Here", "At", "All"],
        })
        
        with pytest.raises(ValueError):
            find_header_row(df)

    def test_detect_snapshot_type_v1(self):
        """Test detecting ECU_V1 snapshot type."""
        df = pd.DataFrame({
            0: ["Frame"],
            1: ["Time"],
            2: ["smc_engine_state"],
        })
        
        result = detect_snapshot_type(df, 0)
        assert result == SnapType.ECU_V1

    def test_detect_snapshot_type_v2(self):
        """Test detecting ECU_V2 snapshot type."""
        df = pd.DataFrame({
            0: ["Frame"],
            1: ["Time"],
            2: ["epm_neng"],
        })
        
        result = detect_snapshot_type(df, 0)
        assert result == SnapType.ECU_V2

    def test_detect_snapshot_type_empty(self):
        """Test returning EMPTY when type not detected."""
        df = pd.DataFrame({
            0: ["Frame"],
            1: ["Time"],
            2: ["unknown_pid"],
        })
        
        result = detect_snapshot_type(df, 0)
        assert result == SnapType.EMPTY


class TestPidExtractor:
    """Tests for pid_extractor module."""

    def test_extract_pid_info(self):
        """Test extracting PID information."""
        df = pd.DataFrame({
            0: ["", "Frame", ""],
            1: ["", "Time", ""],
            2: ["Test Description", "TestPID", "rpm"],
        })
        
        result = extract_pid_info(df, header_row_idx=1, start_col=2)
        
        assert "TestPID" in result
        assert result["TestPID"]["Description"] == "Test Description"
        assert result["TestPID"]["Unit"] == "rpm"

    def test_to_str_handles_nan(self):
        """Test _to_str handles NaN values."""
        assert _to_str(None) == ""
        assert _to_str(float('nan')) == ""
        assert _to_str("test") == "test"
        assert _to_str("  spaces  ") == "spaces"


class TestDataCleaner:
    """Tests for data_cleaner module."""

    def test_scrub_snapshot_basic(self):
        """Test basic snapshot scrubbing."""
        df = pd.DataFrame({
            0: ["Description", "OldFrame", "Unit", "0", "1"],
            1: ["Desc", "OldTime", "s", "0.0", "1.0"],
            2: ["PID Desc", "TestPID", "rpm", "100", "200"],
        })
        pid_info = {}
        
        result = scrub_snapshot(df, header_row_idx=1, pid_info=pid_info)
        
        assert "Frame" in result.columns
        assert "Time" in result.columns
        assert result["Frame"].iloc[0] == 0

    def test_remove_unsupported_pids(self):
        """Test removal of unsupported PIDs."""
        df = pd.DataFrame({
            "Frame": [0, 1],
            "Time": [0.0, 1.0],
            "GoodPID": [100, 200],
            "BadPID": ["Not supported", "Not supported"],
        })
        pid_info = {"GoodPID": {}, "BadPID": {}}
        
        result = remove_unsupported_pids(df, pid_info)
        
        assert "GoodPID" in result.columns
        assert "BadPID" not in result.columns
        assert "BadPID" not in pid_info


class TestTimeProcessor:
    """Tests for time_processor module."""

    def test_process_time_column(self):
        """Test time column processing."""
        df = pd.DataFrame({
            "Frame": [0, 1, 2],
            "Time": [0, 1, 2],
        })
        
        result = process_time_column(df)
        
        assert result["Time"].iloc[0] == 0.0
        assert result["Time"].iloc[1] == 1.0

    def test_find_engine_hours_v1(self):
        """Test finding engine hours for V1 snapshot."""
        df = pd.DataFrame({
            "Frame": [0, 1],
            "EUD_Engine_run_time_nvv": [36000, 36000],  # 10 hours in seconds
        })
        pid_info = {"EUD_Engine_run_time_nvv": {"Unit": "seconds"}}
        
        result = find_engine_hours(df, SnapType.ECU_V1, pid_info)
        
        assert result == 10.0

    def test_find_idle_time(self):
        """Test finding idle time."""
        df = pd.DataFrame({
            "Frame": [0, 1],
            "EUD_Engine_idle_time_nvv": [3600, 3600],  # 1 hour in seconds
        })
        pid_info = {"EUD_Engine_idle_time_nvv": {"Unit": "seconds"}}
        
        result = find_idle_time(df, pid_info)
        
        assert result == 1.0

    def test_calculate_mdp_success(self):
        """Test MDP success rate calculation."""
        df = pd.DataFrame({
            "Frame": [0],
            "I_C_Mdp_nb_update_success_nvv": [90],
            "I_C_Mdp_nb_update_failure_nvv": [10],
        })
        
        result = calculate_mdp_success(df)
        
        assert result == 90.0

    def test_calculate_mdp_success_zero_total(self):
        """Test MDP success with zero total updates."""
        df = pd.DataFrame({
            "Frame": [0],
            "I_C_Mdp_nb_update_success_nvv": [0],
            "I_C_Mdp_nb_update_failure_nvv": [0],
        })
        
        result = calculate_mdp_success(df)
        
        assert result == 0.0


class TestSnapshotIntegration:
    """Integration tests for the Snapshot class."""

    def test_snapshot_import(self):
        """Test that Snapshot can be imported from the package."""
        from domain.snapshot import Snapshot
        assert Snapshot is not None
