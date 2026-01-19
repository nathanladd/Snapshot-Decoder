# Version 2 Planning Document

> **Target:** PySide6-only UI with clean architecture separation  
> **Branch:** `version_two`  
> **Approach:** Build domain/controllers first, add UI last, test incrementally

---

## Current Architecture Analysis

### Pain Points Identified

1. **`ui/app.py` is monolithic (1085 lines)**
   - Mixes UI construction, state management, event handling, and business logic
   - Hard to test individual components
   - Changes risk unintended side effects

2. **`quick_charts.py` directly manipulates UI widgets**
   - `apply_quick_chart_setup()` reaches into `main_app` to set listboxes, variables
   - Creates tight coupling between chart logic and Tkinter widgets
   - Example from current code:
     ```python
     def apply_quick_chart_setup(main_app, ...):
         main_app.primary_list.delete(0, 'end')  # Direct UI manipulation!
         main_app.primary_series = primary_pids
     ```

3. **Memory/State Retention Issues**
   - `working_config` retains stale data when switching chart types
   - `primary_ticks`, `primary_tick_labels` persist across chart changes
   - Status charts add columns to `snapshot` DataFrame that pollute later charts
   - No explicit reset of chart-specific state between chart renders

4. **Chart type logic scattered**
   - `chart_renderer.py` (667 lines) handles all chart types in one file
   - Status chart creates display columns directly in snapshot data

5. **`snapshot.py` is monolithic (548 lines)**
   - Mixes file loading, header parsing, type identification, PID extraction, data cleaning, and derived value calculations
   - Multiple responsibilities in one class make testing and maintenance difficult
   - Logical groupings that could be separate modules:
     - Header parsing (~100 lines)
     - Snapshot type identification (~50 lines)
     - PID metadata extraction (~50 lines)
     - Data cleaning/scrubbing (~100 lines)
     - Derived value calculations (~150 lines)

---

## V2 Architecture (PySide6-Only)

### Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (PySide6)                     │
│  - QMainWindow, QWidgets                                │
│  - Connects to controller via Qt signals/slots          │
│  - No business logic                                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Application Layer (Controllers)            │
│  - AppController (QObject): orchestrates app actions    │
│  - ChartController: manages chart state & rendering     │
│  - Emits Qt signals for UI updates                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Domain Layer                         │
│  - Snapshot: data loading and parsing                   │
│  - ChartConfig: chart configuration dataclass           │
│  - ChartState: explicit state management (NEW)          │
│  - QuickChartDefinitions: declarative, no UI refs       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Rendering Layer                       │
│  - BaseRenderer: abstract interface                     │
│  - LineRenderer, BarRenderer, BubbleRenderer, etc.      │
│  - Each chart type in its own file                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                    │
│  - file_io: Excel readers, PDF export                   │
│  - Matplotlib backend for chart rendering               │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Domain Layer Refactoring

**Goal:** Clean separation of chart logic, fully testable without any UI.

### 1.1 Refactor Quick Charts to Declarative Definitions

**Current problem:** Functions manipulate UI directly

**Solution:** Pure data definitions that describe what a chart should contain

```python
# domain/quick_charts/definitions.py
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class QuickChartDef:
    """Declarative definition of a quick chart - no UI references."""
    action_id: str
    title: str
    primary_pids: List[str]
    primary_range: Optional[Tuple[float, float]] = None
    secondary_pids: List[str] = None
    secondary_range: Optional[Tuple[float, float]] = None
    chart_type: str = "line"
    show_legend: bool = True
    primary_ticks: Optional[List[float]] = None
    primary_tick_labels: Optional[List[str]] = None

# Example definition
V1_BATTERY_TEST = QuickChartDef(
    action_id="V1_BATTERY_TEST",
    title="Battery Voltage vs RPM",
    primary_pids=["P_L_Battery_raw"],
    primary_range=(0, 18),
    secondary_pids=["IN_Engine_cycle_speed"],
    secondary_range=(-50, 6250),
)
```

**Files to create:**
- `domain/quick_charts/__init__.py`
- `domain/quick_charts/definitions.py` — all chart definitions as dataclasses
- `domain/quick_charts/builders.py` — factory to build `ChartConfig` from definitions

**Test checkpoint:** Unit test verifying `ChartConfigBuilder.build()` returns valid `ChartConfig`.

---

### 1.2 Split Chart Renderers by Type

**Current:** `chart_renderer.py` (667 lines) handles all chart types

**Solution:** One renderer class per chart type

```python
# rendering/base_renderer.py
from abc import ABC, abstractmethod
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from domain.chart_config import ChartConfig

class BaseRenderer(ABC):
    def __init__(self, config: ChartConfig):
        self.config = config
    
    @abstractmethod
    def render(self, figure: Figure) -> Tuple[Axes, Optional[Axes]]:
        """Render chart to figure, return (primary_ax, secondary_ax)."""
        pass
    
    def render_thumbnail(self, figsize=(4, 2), dpi=50) -> Figure:
        """Render a small preview thumbnail."""
        # Common thumbnail logic
        pass
```

**Files to create:**
- `rendering/__init__.py`
- `rendering/base_renderer.py` — abstract base class
- `rendering/line_renderer.py`
- `rendering/bar_renderer.py`
- `rendering/bubble_renderer.py`
- `rendering/status_renderer.py`

**Test checkpoint:** Each renderer can render to a `Figure` without errors.

---

### 1.3 Fix Memory Issues with ChartState

**Root cause:** State scattered across `main_app` attributes, never explicitly reset

**Solution:** Centralized `ChartState` class with explicit reset

```python
# domain/chart_state.py
from dataclasses import dataclass, field
from typing import Optional, List
from domain.chart_config import ChartConfig

@dataclass
class ChartState:
    """Manages all transient chart state with explicit reset capability."""
    
    # Current chart configuration
    config: Optional[ChartConfig] = None
    
    # Axis series selections
    primary_series: List[str] = field(default_factory=list)
    secondary_series: List[str] = field(default_factory=list)
    
    # Axis range settings
    primary_auto: bool = True
    primary_min: Optional[float] = None
    primary_max: Optional[float] = None
    secondary_auto: bool = True
    secondary_min: Optional[float] = None
    secondary_max: Optional[float] = None
    
    # Custom ticks (for status charts, etc.)
    primary_ticks: Optional[List[float]] = None
    primary_tick_labels: Optional[List[str]] = None
    
    # Chart type
    chart_type: str = "line"
    show_legend: bool = True
    
    def reset(self):
        """Reset ALL transient state for a fresh chart."""
        self.config = None
        self.primary_series = []
        self.secondary_series = []
        self.primary_auto = True
        self.primary_min = None
        self.primary_max = None
        self.secondary_auto = True
        self.secondary_min = None
        self.secondary_max = None
        self.primary_ticks = None
        self.primary_tick_labels = None
        self.chart_type = "line"
        self.show_legend = True
    
    def reset_for_chart_type_change(self):
        """Reset state that doesn't transfer between chart types."""
        self.primary_ticks = None
        self.primary_tick_labels = None
```

**Test checkpoint:** Verify `reset()` clears all state; verify switching chart types calls appropriate reset.

---

### 1.4 Refactor Snapshot into Multiple Modules

**Current problem:** `snapshot.py` (548 lines) handles too many responsibilities

**Solution:** Split into focused modules within a `domain/snapshot/` package

```
domain/snapshot/
├── __init__.py          # Exports Snapshot class
├── snapshot.py          # Main Snapshot class (coordinator, ~80 lines)
├── header_parser.py     # Header parsing logic
├── type_detector.py     # Snapshot type identification
├── pid_extractor.py     # PID metadata extraction
├── data_cleaner.py      # DataFrame cleaning/scrubbing
└── derived_values.py    # Engine hours, idle time, MDP calculations
```

#### 1.4.1 `header_parser.py` — Header Parsing

```python
# domain/snapshot/header_parser.py
from typing import List, Tuple
import pandas as pd
from domain.constants import HEADER_LABELS

class HeaderParser:
    """Parses snapshot file header information."""
    
    @staticmethod
    def parse(df: pd.DataFrame, max_rows: int = 5) -> List[Tuple[str, str]]:
        """
        Parse header rows as label/value pairs.
        Returns ordered list of (label, value).
        """
        results = []
        # ... existing _parse_header logic ...
        return results
    
    @staticmethod
    def normalize_label(text: str) -> str:
        """Normalize label to canonical display name."""
        # ... existing _normalize_label logic ...
        pass
    
    @staticmethod
    def find_date_time(header_list: List[Tuple[str, str]]) -> str:
        """Extract date/time from parsed header list."""
        for label, value in header_list:
            if label == "Date / Time":
                return value
        return ""
```

**Test checkpoint:** Unit test header parsing with sample DataFrames.

---

#### 1.4.2 `type_detector.py` — Snapshot Type Detection

**Current problem:** Single PID matching is fragile—one PID could appear in multiple snapshot types

**Solution:** Require multiple PID matches per type for reliable identification

```python
# domain/constants.py - NEW structure for multi-PID matching
PID_SIGNATURES: dict[SnapType, set[str]] = {
    SnapType.ECU_V1: {
        "p_l_battery_raw",
        "in_engine_cycle_speed",
        "smc_engine_state",
        "p_l_rail_actual_raw",
        "p_l_rail_demand",
    },
    SnapType.ECU_V2: {
        "battu_u",
        "engda_tiengon",
        "n_eng",
        "railp_pdes",
        "railp_p",
    },
    SnapType.EUD_V1: {
        "p_l_egr_close_pos_learnt_nvv",
        "eud_engine_run_time_total_nvv",
        "p_l_atm_pressure",
    },
    # Add more types as needed
}

# Minimum matches required to identify a type
MIN_PID_MATCHES = 2
```

```python
# domain/snapshot/type_detector.py
import pandas as pd
from typing import Tuple, Optional
from domain.snaptypes import SnapType
from domain.constants import PID_SIGNATURES, MIN_PID_MATCHES

class TypeDetector:
    """Identifies snapshot type from DataFrame content using multi-PID matching."""
    
    @staticmethod
    def find_header_row(df: pd.DataFrame) -> int:
        """Find the row index containing PID names."""
        all_known_pids = set()
        for pids in PID_SIGNATURES.values():
            all_known_pids.update(pids)
        
        for i in range(min(len(df), 15)):
            row_values = set(df.iloc[i].astype(str).str.strip().str.lower().tolist())
            matches = row_values & all_known_pids
            if len(matches) >= MIN_PID_MATCHES:
                return i
        raise ValueError("Couldn't locate header row with known PIDs")
    
    @staticmethod
    def identify_type(df: pd.DataFrame, header_row_idx: int) -> Tuple[SnapType, int]:
        """
        Identify snapshot type by counting PID matches per type.
        
        Returns:
            (SnapType, match_count) - type with most matches (if >= MIN_PID_MATCHES)
            (SnapType.EMPTY, 0) - if no type has enough matches
        """
        row_values = set(df.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist())
        
        best_type = SnapType.EMPTY
        best_count = 0
        
        for snap_type, signature_pids in PID_SIGNATURES.items():
            matches = row_values & signature_pids
            if len(matches) > best_count:
                best_count = len(matches)
                best_type = snap_type
        
        if best_count >= MIN_PID_MATCHES:
            return (best_type, best_count)
        return (SnapType.EMPTY, 0)
```

**Benefits:**
- More reliable type identification (requires 2+ matches)
- Returns match count for confidence scoring
- Easy to add new types by expanding `PID_SIGNATURES`
- Can tune `MIN_PID_MATCHES` threshold as needed

**Test checkpoint:** Unit test type detection with known snapshot samples, verify correct type with match counts.

---

#### 1.4.3 `pid_extractor.py` — PID Metadata Extraction

```python
# domain/snapshot/pid_extractor.py
from typing import Dict
import pandas as pd
from domain.constants import UNIT_NORMALIZATION

class PidExtractor:
    """Extracts PID descriptions and units from DataFrame."""
    
    @staticmethod
    def extract(df: pd.DataFrame, header_row_idx: int, start_col: int = 2) -> Dict[str, Dict[str, str]]:
        """
        Extract PID name -> {Description, Unit} mapping.
        """
        pid_info = {}
        # ... existing _extract_pid_descriptions logic ...
        return pid_info
    
    @staticmethod
    def update_unit(pid_info: Dict, pid_name: str, new_unit: str) -> None:
        """Update unit for a specific PID."""
        if pid_name in pid_info:
            pid_info[pid_name]["Unit"] = new_unit
```

**Test checkpoint:** Unit test PID extraction returns correct metadata.

---

#### 1.4.4 `data_cleaner.py` — DataFrame Cleaning

```python
# domain/snapshot/data_cleaner.py
import pandas as pd
from typing import Dict, Set

class DataCleaner:
    """Cleans and normalizes snapshot DataFrames."""
    
    @staticmethod
    def scrub(raw_df: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
        """
        Process raw DataFrame:
        - Set column headers
        - Rename Frame/Time columns
        - Trim to Frame == 0
        - Convert time to seconds
        """
        # ... existing _scrub_snapshot logic ...
        pass
    
    @staticmethod
    def remove_unsupported_pids(df: pd.DataFrame, pid_info: Dict) -> pd.DataFrame:
        """Remove columns containing 'Not supported' values."""
        # ... existing _remove_unsupported_pids logic ...
        pass
    
    @staticmethod
    def clean_column_apostrophes(df: pd.DataFrame, col_name: str) -> None:
        """Remove leading apostrophes from string values."""
        # ... existing _clean_column_apostrophes logic ...
        pass
```

**Test checkpoint:** Unit test cleaning with malformed data.

---

#### 1.4.5 `derived_values.py` — Calculated Values

```python
# domain/snapshot/derived_values.py
import pandas as pd
from typing import Dict
from domain.snaptypes import SnapType
from domain.constants import ENGINE_HOURS_COLUMNS

class ValueExtractor:
    """Finds and/or calculates derived values from snapshot data."""
    
    @staticmethod
    def find_engine_hours(df: pd.DataFrame, snap_type: SnapType, pid_info: Dict) -> float:
        """Extract engine hours from snapshot."""
        column_name = ENGINE_HOURS_COLUMNS.get(snap_type)
        if not column_name or column_name not in df.columns:
            return 0.0
        # ... existing _find_engine_hours logic ...
        pass
    
    @staticmethod
    def find_idle_time(df: pd.DataFrame, pid_info: Dict) -> float:
        """Extract idle time from snapshot."""
        # ... existing _find_idle_time logic ...
        pass
    
    @staticmethod
    def calculate_mdp_success(df: pd.DataFrame) -> float:
        """Calculate MDP success rate."""
        # ... existing _calculate_mdp_success logic ...
        pass
```

**Test checkpoint:** Unit test calculations with known values.

---

#### 1.4.6 Refactored `snapshot.py` — Coordinator

```python
# domain/snapshot/snapshot.py
from __future__ import annotations
import os
from typing import Optional, Dict, List, Tuple
import pandas as pd

from domain.snaptypes import SnapType
from domain.snapshot.header_parser import HeaderParser
from domain.snapshot.type_detector import TypeDetector
from domain.snapshot.pid_extractor import PidExtractor
from domain.snapshot.data_cleaner import DataCleaner
from domain.snapshot.derived_values import ValueExtractor
from file_io.reader_excel import load_xls, load_xlsx

class Snapshot:
    """
    Domain entity representing a loaded and parsed snapshot.
    Coordinates parsing using specialized modules.
    """
    
    def __init__(self, path: str):
        self.file_path: str = path
        self.file_name: str = os.path.basename(path)
        self.raw_table: Optional[pd.DataFrame] = None
        self.snapshot: Optional[pd.DataFrame] = None
        self.date_time: Optional[str] = None
        self.hours: float = 0.0
        self.header_list: List[Tuple[str, str]] = []
        self.pid_info: Dict[str, Dict[str, str]] = {}
        self.snapshot_type: SnapType = SnapType.EMPTY
        self.mdp_success_rate: float = 0.0
        self.idle_time: float = 0.0
    
    @classmethod
    def load(cls, path: str) -> Snapshot:
        """Load and parse a snapshot from file."""
        instance = cls(path)
        instance._load_and_parse()
        return instance
    
    def _load_and_parse(self):
        """Orchestrate the parsing pipeline."""
        # Load raw data
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext == ".xlsx":
            self.raw_table = load_xlsx(self.file_path)
        elif ext == ".xls":
            self.raw_table = load_xls(self.file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
        
        if self.raw_table is None or self.raw_table.empty:
            raise ValueError("No data table found in workbook.")
        
        # Parse using specialized modules
        self.header_list = HeaderParser.parse(self.raw_table)
        self.date_time = HeaderParser.find_date_time(self.header_list)
        
        header_row_idx = TypeDetector.find_header_row(self.raw_table)
        self.snapshot_type = TypeDetector.identify_type(self.raw_table, header_row_idx)
        
        self.pid_info = PidExtractor.extract(self.raw_table, header_row_idx)
        
        self.snapshot = DataCleaner.scrub(self.raw_table, header_row_idx)
        self.snapshot = DataCleaner.remove_unsupported_pids(self.snapshot, self.pid_info)
        
        self.hours = ValueExtractor.find_engine_hours(self.snapshot, self.snapshot_type, self.pid_info)
        self.idle_time = ValueExtractor.find_idle_time(self.snapshot, self.pid_info)
        self.mdp_success_rate = ValueExtractor.calculate_mdp_success(self.snapshot)
        
        # Type-specific adjustments
        self._apply_type_specific_fixes()
    
    def _apply_type_specific_fixes(self):
        """Apply snapshot-type-specific data corrections."""
        if self.snapshot_type == SnapType.ECU_V1:
            PidExtractor.update_unit(self.pid_info, "SMC_ENGINE_STATE", 
                "[0]Off   [1]Cranking   [2]Running   [3]Stalling")
        
        if self.snapshot_type == SnapType.ECU_V2:
            if "BattU_u" in self.snapshot.columns:
                self.snapshot["BattU_u"] = pd.to_numeric(self.snapshot["BattU_u"], errors="coerce") / 1000
                PidExtractor.update_unit(self.pid_info, "BattU_u", "Volts")
```

**Benefits:**
- Main `Snapshot` class is now ~80 lines (down from 548)
- Each module is independently testable
- Clear separation of concerns
- Easier to modify one aspect without affecting others

**Test checkpoint:** Integration test that `Snapshot.load()` still works end-to-end.

---

### 1.5 Upgrade reader_excel.py with Layout Detection

**Current problem:** Files may have data in two orientations:
- **Row-oriented (standard):** PID names in a row, data flows down
- **Column-oriented (transposed):** PID names in a column, data flows right

Current reader assumes row-oriented layout only.

**Solution:** Detect layout by scanning for known PIDs in both orientations, transpose if needed

```python
# file_io/reader_excel.py
from typing import Tuple, Optional
import pandas as pd
from domain.constants import PID_SIGNATURES, MIN_PID_MATCHES

class LayoutDetector:
    """Detects whether PIDs are in rows or columns."""
    
    @classmethod
    def _get_all_known_pids(cls) -> set[str]:
        """Flatten all PIDs from PID_SIGNATURES into one set."""
        all_pids = set()
        for pids in PID_SIGNATURES.values():
            all_pids.update(pids)
        return all_pids
    
    @classmethod
    def detect_layout(cls, df: pd.DataFrame) -> Tuple[str, Optional[int]]:
        """
        Scan DataFrame for known PIDs to determine orientation.
        
        Returns:
            ("row", row_index) if PIDs found in a row
            ("column", col_index) if PIDs found in a column
            ("unknown", None) if no PIDs found
        """
        known_pids = cls._get_all_known_pids()
        
        # Scan rows (check first 15 rows)
        for row_idx in range(min(len(df), 15)):
            row_values = set(df.iloc[row_idx].astype(str).str.strip().str.lower().tolist())
            matches = row_values & known_pids
            if len(matches) >= MIN_PID_MATCHES:
                return ("row", row_idx)
        
        # Scan columns (check first 15 columns)
        for col_idx in range(min(len(df.columns), 15)):
            col_values = set(df.iloc[:, col_idx].astype(str).str.strip().str.lower().tolist())
            matches = col_values & known_pids
            if len(matches) >= MIN_PID_MATCHES:
                return ("column", col_idx)
        
        return ("unknown", None)


def normalize_layout(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame has PIDs as column headers.
    Transposes if PIDs are detected in a column instead of a row.
    """
    layout, index = LayoutDetector.detect_layout(df)
    
    if layout == "column":
        # PIDs are in a column - transpose the data
        df = df.T.reset_index(drop=True)
    
    return df


def load_xlsx(path: str) -> pd.DataFrame:
    """Read XLSX file and normalize layout."""
    df = pd.read_excel(path, header=None, engine="openpyxl")
    return normalize_layout(df)


def load_xls(path: str) -> pd.DataFrame:
    """Read XLS (UTF-16 tab-delimited) file and normalize layout."""
    with open(path, "r", encoding="utf-16") as f:
        text = f.read()
    rows = text.split("\n")
    data = [r.split("\t") for r in rows]
    df = pd.DataFrame(data)
    return normalize_layout(df)
```

**Key points:**
- Uses `PID_SIGNATURES` from constants (shared with `TypeDetector`)
- Requires `MIN_PID_MATCHES` (default 2) to avoid false positives
- Scans first 15 rows/columns (configurable)
- Transpose happens before any other processing
- Existing snapshot parsing code unchanged - it receives normalized DataFrame

**Files to modify:**
- `file_io/reader_excel.py` — add `LayoutDetector` class and `normalize_layout()`
- `domain/constants.py` — replace `PID_KEY` with `PID_SIGNATURES` and `MIN_PID_MATCHES`

**Test checkpoint:** Unit test with both row-oriented and column-oriented sample files.

---

## Phase 2: Application Layer (Controllers)

**Goal:** UI-agnostic orchestration using Qt signals for communication.

### 2.1 SnapshotLoader (QThread with Progress)

**Problem:** Large snapshot files can take several seconds to load, freezing the UI

**Solution:** Load snapshots in a dedicated `QThread` with progress signals

```python
# controllers/snapshot_loader.py
from PySide6.QtCore import QThread, Signal
from domain.snapshot import Snapshot

class SnapshotLoader(QThread):
    """Background thread for loading snapshots with progress updates."""
    
    # Signals
    progress = Signal(int, str)      # (percent, message)
    finished = Signal(object)         # Snapshot on success
    error = Signal(str)               # Error message on failure
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation (checked between phases)."""
        self._cancelled = True
    
    def run(self):
        try:
            self.progress.emit(5, "Reading file...")
            # Phase 1: Load raw data
            raw_df = self._load_raw_file()
            if self._cancelled:
                return
            
            self.progress.emit(20, "Detecting layout...")
            # Phase 2: Normalize layout (transpose if needed)
            normalized_df = normalize_layout(raw_df)
            if self._cancelled:
                return
            
            self.progress.emit(35, "Parsing headers...")
            # Phase 3: Parse header info
            header_list = HeaderParser.parse(normalized_df)
            if self._cancelled:
                return
            
            self.progress.emit(50, "Identifying snapshot type...")
            # Phase 4: Detect type
            header_row = TypeDetector.find_header_row(normalized_df)
            snap_type, confidence = TypeDetector.identify_type(normalized_df, header_row)
            if self._cancelled:
                return
            
            self.progress.emit(65, "Extracting PID metadata...")
            # Phase 5: Extract PIDs
            pid_info = PidExtractor.extract(normalized_df, header_row)
            if self._cancelled:
                return
            
            self.progress.emit(80, "Cleaning data...")
            # Phase 6: Scrub DataFrame
            cleaned_df = DataCleaner.scrub(normalized_df, header_row)
            cleaned_df = DataCleaner.remove_unsupported_pids(cleaned_df, pid_info)
            if self._cancelled:
                return
            
            self.progress.emit(90, "Calculating derived values...")
            # Phase 7: Derived values
            hours = ValueExtractor.find_engine_hours(cleaned_df, snap_type, pid_info)
            idle_time = ValueExtractor.find_idle_time(cleaned_df, pid_info)
            mdp_rate = ValueExtractor.calculate_mdp_success(cleaned_df)
            
            self.progress.emit(100, "Complete")
            
            # Build and emit Snapshot object
            snapshot = self._build_snapshot(
                cleaned_df, header_list, pid_info, snap_type, hours, idle_time, mdp_rate
            )
            self.finished.emit(snapshot)
            
        except Exception as e:
            self.error.emit(str(e))
```

**UI Integration:**

```python
# In MainWindow or AppController
def load_snapshot(self, file_path: str):
    """Start background snapshot loading with progress dialog."""
    self.loader = SnapshotLoader(file_path)
    
    # Create progress dialog
    self.progress_dialog = QProgressDialog(
        "Loading snapshot...", "Cancel", 0, 100, self
    )
    self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
    self.progress_dialog.setAutoClose(True)
    
    # Connect signals
    self.loader.progress.connect(self._on_load_progress)
    self.loader.finished.connect(self._on_load_finished)
    self.loader.error.connect(self._on_load_error)
    self.progress_dialog.canceled.connect(self.loader.cancel)
    
    # Start loading
    self.loader.start()

def _on_load_progress(self, percent: int, message: str):
    self.progress_dialog.setValue(percent)
    self.progress_dialog.setLabelText(message)

def _on_load_finished(self, snapshot: Snapshot):
    self.snapshot = snapshot
    self.snapshot_loaded.emit(snapshot)

def _on_load_error(self, error_msg: str):
    self.progress_dialog.close()
    QMessageBox.critical(self, "Load Error", error_msg)
```

**Benefits:**
- UI remains responsive during load
- User sees meaningful progress phases
- Cancel button allows aborting long loads
- Error handling with user feedback

**Test checkpoint:** Unit test loader emits correct progress sequence; integration test with real file.

---

### 2.2 Logging Infrastructure

**Goals:**
- Chain of custody records for loaded snapshots
- Diagnostic logging for troubleshooting
- Toggleable verbose mode for detailed debugging
- Rotating log files in app data folder

#### 2.2.1 Log Configuration

```python
# infrastructure/logging_config.py
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# App data folder location
def get_log_directory() -> Path:
    """Get or create the log directory in user's app data."""
    if os.name == 'nt':  # Windows
        app_data = Path(os.environ.get('APPDATA', Path.home()))
    else:  # macOS/Linux
        app_data = Path.home() / '.config'
    
    log_dir = app_data / 'Snapshot Decoder' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

# Log levels
NORMAL_LEVEL = logging.INFO
VERBOSE_LEVEL = logging.DEBUG

# Rotating file configuration
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB per file
BACKUP_COUNT = 10               # Keep last 10 log files

def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        verbose: If True, enable DEBUG level logging with extra details
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('snapshot_decoder')
    logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    log_file = get_log_directory() / 'snapshot_decoder.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(VERBOSE_LEVEL if verbose else NORMAL_LEVEL)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def set_verbose_mode(logger: logging.Logger, verbose: bool):
    """Toggle verbose logging at runtime."""
    level = VERBOSE_LEVEL if verbose else NORMAL_LEVEL
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setLevel(level)
```

#### 2.2.2 What Gets Logged

**Chain of Custody (always logged at INFO level):**

```python
# Example log entries for a snapshot load
logger.info(f"=== Loading snapshot: {file_path} ===")
logger.info(f"File size: {file_size_kb:.1f} KB")
logger.info(f"Snapshot type detected: {snap_type.name} (confidence: {match_count} PIDs)")
logger.info(f"Date/Time from file: {date_time}")
logger.info(f"Engine hours: {hours:.1f}")
logger.info(f"Idle time: {idle_time:.1f}")
logger.info(f"MDP success rate: {mdp_rate:.1f}%")
logger.info(f"Total PIDs loaded: {len(pid_info)}")
logger.info(f"=== Load complete ===")
```

**Verbose/Debug Details (only when verbose=True):**

```python
# DataFrame shapes
logger.debug(f"Raw DataFrame shape: {raw_df.shape}")
logger.debug(f"Cleaned DataFrame shape: {cleaned_df.shape}")

# PID names
logger.debug(f"PID names: {list(pid_info.keys())}")

# Layout detection
logger.debug(f"Layout detected: {layout} at index {index}")
logger.debug(f"Header row found at index: {header_row_idx}")

# Type detection details
logger.debug(f"PID signature matches: {matches}")

# Parsing phases
logger.debug(f"Header parsing found {len(header_list)} entries")
logger.debug(f"Removed {removed_count} unsupported PIDs")

# Errors/warnings
logger.warning(f"Could not parse engine hours from column: {col_name}")
logger.error(f"Failed to load file: {error_message}")
```

#### 2.2.3 Integration with SnapshotLoader

```python
# controllers/snapshot_loader.py
from infrastructure.logging_config import logging

class SnapshotLoader(QThread):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.logger = logging.getLogger('snapshot_decoder.loader')
    
    def run(self):
        self.logger.info(f"=== Loading snapshot: {self.file_path} ===")
        file_size = os.path.getsize(self.file_path) / 1024
        self.logger.info(f"File size: {file_size:.1f} KB")
        
        try:
            # Phase 1
            self.progress.emit(5, "Reading file...")
            raw_df = self._load_raw_file()
            self.logger.debug(f"Raw DataFrame shape: {raw_df.shape}")
            
            # ... (each phase logs its activity)
            
            self.logger.info(f"Snapshot type: {snap_type.name} (confidence: {confidence})")
            self.logger.info(f"Engine hours: {hours:.1f}")
            self.logger.info(f"Total PIDs: {len(pid_info)}")
            self.logger.debug(f"PID names: {list(pid_info.keys())}")
            self.logger.info(f"=== Load complete ===")
            
        except Exception as e:
            self.logger.error(f"Load failed: {e}", exc_info=True)
            self.error.emit(str(e))
```

#### 2.2.4 UI Toggle for Verbose Mode

```python
# In settings or menu
class MainWindow(QMainWindow):
    def __init__(self):
        # ...
        self.verbose_logging = False
        self.logger = logging.getLogger('snapshot_decoder')
    
    def toggle_verbose_logging(self, enabled: bool):
        """Menu action to toggle verbose logging."""
        self.verbose_logging = enabled
        set_verbose_mode(self.logger, enabled)
        self.logger.info(f"Verbose logging {'enabled' if enabled else 'disabled'}")
```

**Log file location:** `%APPDATA%/Snapshot Decoder/logs/snapshot_decoder.log`

**Rotation:** 10 files × 5 MB = 50 MB max disk usage

**Test checkpoint:** Unit test log file creation, rotation, and verbose toggle.

---

### 2.3 Console Panel (Live Log Viewer)

**Goals:**
- Display log messages in real-time within the UI
- Support overwritable progress lines for batch operations
- Color-code messages by severity level
- Toggle visibility via View menu

#### 2.3.1 Log Console Widget

```python
# ui/log_console.py
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat
from PySide6.QtCore import Slot

class LogConsole(QPlainTextEdit):
    """
    Live log viewer with overwrite support for progress updates.
    
    Features:
    - Color-coded log levels
    - Overwritable lines for batch progress (e.g., "Processing 3/50...")
    - Auto-scroll to bottom
    - Memory-limited buffer
    """
    
    COLORS = {
        'DEBUG': '#888888',    # Gray
        'INFO': '#ffffff',     # White
        'WARNING': '#ffcc00',  # Yellow
        'ERROR': '#ff4444',    # Red
        'CRITICAL': '#ff0000', # Bright red
    }
    
    def __init__(self, max_lines: int = 1000):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumBlockCount(max_lines)
        self._last_was_progress = False
        
        # Dark background for console look
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
    
    @Slot(str, str, bool)
    def log(self, level: str, message: str, overwrite: bool = False):
        """
        Append a log message, optionally overwriting the last line.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: The log message text
            overwrite: If True, replace the last line (for progress updates)
        """
        if overwrite and self._last_was_progress:
            self._remove_last_line()
        
        # Format with color
        color = self.COLORS.get(level, '#ffffff')
        formatted = f'<span style="color:{color}">{message}</span>'
        self.appendHtml(formatted)
        
        self._last_was_progress = overwrite
        self._scroll_to_bottom()
    
    def _remove_last_line(self):
        """Remove the last line of text."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # Remove trailing newline
    
    def _scroll_to_bottom(self):
        """Auto-scroll to show latest message."""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_console(self):
        """Clear all log messages."""
        self.clear()
        self._last_was_progress = False
```

#### 2.3.2 Qt Log Handler (Bridge to Python Logging)

```python
# infrastructure/logging_config.py (addition)
import logging
from PySide6.QtCore import QObject, Signal

class QtLogHandler(logging.Handler, QObject):
    """
    Routes Python logging messages to a Qt signal.
    
    This allows log messages from any thread to safely update the UI
    via Qt's signal/slot mechanism.
    """
    
    # Signal: (level_name, formatted_message, is_progress)
    log_emitted = Signal(str, str, bool)
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self._progress_prefix = None
    
    def set_progress_prefix(self, prefix: str | None):
        """
        Set a prefix that identifies progress messages (overwritable).
        
        Example: set_progress_prefix("Processing file")
        Then any message starting with "Processing file" will overwrite.
        """
        self._progress_prefix = prefix
    
    def emit(self, record: logging.LogRecord):
        """Emit log record as Qt signal."""
        msg = self.format(record)
        is_progress = (
            self._progress_prefix is not None 
            and msg.startswith(self._progress_prefix)
        )
        self.log_emitted.emit(record.levelname, msg, is_progress)
```

#### 2.3.3 Integration with MainWindow

```python
# ui/main_window.py
from ui.log_console import LogConsole
from infrastructure.logging_config import setup_logging, QtLogHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_logging()
        self._setup_ui()
    
    def _setup_logging(self):
        """Configure logging with both file and UI handlers."""
        self.logger = setup_logging(verbose=False)
        
        # Add Qt handler for UI console
        self.qt_handler = QtLogHandler()
        self.qt_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.logger.addHandler(self.qt_handler)
    
    def _setup_ui(self):
        # ... other UI setup ...
        
        # Console as dockable panel
        self.log_console = LogConsole()
        self.console_dock = QDockWidget("Console", self)
        self.console_dock.setWidget(self.log_console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)
        
        # Connect Qt handler signal to console
        self.qt_handler.log_emitted.connect(self.log_console.log)
        
        # View menu toggle
        self.view_menu.addAction(self.console_dock.toggleViewAction())
```

#### 2.3.4 Batch Processing with Progress Overwrite

```python
# Example: Processing multiple snapshot files
class BatchProcessor:
    def __init__(self, logger: logging.Logger, qt_handler: QtLogHandler):
        self.logger = logger
        self.qt_handler = qt_handler
    
    def process_files(self, file_paths: list[str]):
        total = len(file_paths)
        
        # Enable progress line overwriting
        self.qt_handler.set_progress_prefix("Processing file")
        
        for i, path in enumerate(file_paths, 1):
            # This line will overwrite the previous one
            self.logger.info(f"Processing file {i}/{total}: {Path(path).name}")
            
            # Do the actual work...
            snapshot = Snapshot(path)
        
        # Disable overwriting, log final result normally
        self.qt_handler.set_progress_prefix(None)
        self.logger.info(f"Batch complete: {total} files processed")
```

**Console output during batch:**
```
10:30:15 | INFO     | Processing file 47/50: snapshot_047.xlsx  <- overwrites in place
```

**After batch completes:**
```
10:30:15 | INFO     | Processing file 50/50: snapshot_050.xlsx
10:30:16 | INFO     | Batch complete: 50 files processed
```

**Benefits:**
- Real-time visibility into application activity
- Clean progress display without log spam
- Dockable/hideable for user preference
- Thread-safe via Qt signals

**Test checkpoint:** Unit test log console append and overwrite behavior.

---

### 2.4 AppController

```python
# controllers/app_controller.py
from PySide6.QtCore import QObject, Signal
from domain.snapshot import Snapshot
from domain.chart_state import ChartState
from domain.quick_charts.definitions import QUICK_CHART_REGISTRY
from domain.quick_charts.builders import ChartConfigBuilder

class AppController(QObject):
    """Main application controller - orchestrates all app actions."""
    
    # Signals for UI to connect to
    snapshot_loaded = Signal(object)  # emits Snapshot
    chart_updated = Signal(object)    # emits ChartConfig
    error_occurred = Signal(str)      # emits error message
    
    def __init__(self):
        super().__init__()
        self.snapshot: Optional[Snapshot] = None
        self.chart_state = ChartState()
    
    def load_file(self, path: str):
        """Load a snapshot file."""
        try:
            self.snapshot = Snapshot.load(path)
            self.chart_state.reset()
            self.snapshot_loaded.emit(self.snapshot)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def apply_quick_chart(self, action_id: str):
        """Apply a quick chart by its action ID."""
        if not self.snapshot:
            self.error_occurred.emit("No snapshot loaded")
            return
        
        definition = QUICK_CHART_REGISTRY.get(action_id)
        if not definition:
            self.error_occurred.emit(f"Unknown chart: {action_id}")
            return
        
        # Reset state and build new config
        self.chart_state.reset_for_chart_type_change()
        config = ChartConfigBuilder.build(definition, self.snapshot)
        self.chart_state.config = config
        self.chart_updated.emit(config)
    
    def plot_custom_chart(self):
        """Build and plot chart from current state selections."""
        if not self.snapshot:
            return
        
        config = ChartConfigBuilder.from_state(self.chart_state, self.snapshot)
        self.chart_state.config = config
        self.chart_updated.emit(config)
```

**Test checkpoint:** Unit test controller without UI—mock signals, verify correct emissions.

---

### 2.2 ChartController

```python
# controllers/chart_controller.py
from matplotlib.figure import Figure
from domain.chart_config import ChartConfig
from rendering.line_renderer import LineRenderer
from rendering.bar_renderer import BarRenderer
from rendering.bubble_renderer import BubbleRenderer
from rendering.status_renderer import StatusRenderer

class ChartController:
    """Handles chart rendering by delegating to appropriate renderer."""
    
    RENDERERS = {
        "line": LineRenderer,
        "bar": BarRenderer,
        "bubble": BubbleRenderer,
        "status": StatusRenderer,
    }
    
    def render(self, config: ChartConfig, figure: Figure):
        """Render chart config to the given figure."""
        renderer_cls = self.RENDERERS.get(config.chart_type)
        if not renderer_cls:
            raise ValueError(f"Unknown chart type: {config.chart_type}")
        
        renderer = renderer_cls(config)
        return renderer.render(figure)
    
    def render_thumbnail(self, config: ChartConfig):
        """Render a thumbnail preview of the chart."""
        renderer_cls = self.RENDERERS.get(config.chart_type)
        renderer = renderer_cls(config)
        return renderer.render_thumbnail()
```

---

## Phase 3: UI Layer (PySide6)

**Goal:** Build PySide6 UI that connects to controllers via signals/slots.

### 3.1 Main Window Structure

```python
# ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from controllers.app_controller import AppController
from controllers.chart_controller import ChartController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_controller = AppController()
        self.chart_controller = ChartController()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        # Build UI components
        pass
    
    def _connect_signals(self):
        # Connect controller signals to UI slots
        self.app_controller.snapshot_loaded.connect(self._on_snapshot_loaded)
        self.app_controller.chart_updated.connect(self._on_chart_updated)
        self.app_controller.error_occurred.connect(self._on_error)
    
    def _on_snapshot_loaded(self, snapshot):
        """Update UI when snapshot loads."""
        self.header_panel.update(snapshot)
        self.pid_list.populate(snapshot.snapshot.columns)
    
    def _on_chart_updated(self, config):
        """Render chart when config updates."""
        self.chart_controller.render(config, self.figure)
        self.canvas.draw()
```

### 3.2 UI Components (Each in Own File)

| Component | File | Responsibility |
|-----------|------|----------------|
| Header Panel | `ui/header_panel.py` | Show file info, quick chart buttons |
| PID List | `ui/pid_list.py` | Searchable PID selection list |
| Axis Panel | `ui/axis_panel.py` | Primary/secondary axis controls |
| Chart Canvas | `ui/chart_canvas.py` | Matplotlib canvas wrapper |
| Chart Cart | `ui/chart_cart.py` | Multi-chart collection for PDF |
| Toolbar | `ui/toolbar.py` | Zoom, pan, export buttons |

### 3.3 Secondary Windows

Secondary windows share the same `AppController` instance to access snapshot data consistently.

#### 3.3.1 Chart Popup Window

```python
# ui/chart_popup.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from controllers.app_controller import AppController
from controllers.chart_controller import ChartController
from domain.chart_config import ChartConfig

class ChartPopup(QDialog):
    """
    Enlarged chart view in a separate window.
    
    Features:
    - Larger canvas for detailed viewing
    - Edit chart configuration
    - Add to chart cart
    - Export single chart
    """
    
    def __init__(self, app_controller: AppController, config: ChartConfig, parent=None):
        super().__init__(parent)
        self.app_controller = app_controller
        self.chart_controller = ChartController()
        self.config = config
        
        self.setWindowTitle(f"Chart: {config.title}")
        self.resize(900, 700)
        self._setup_ui()
        self._render_chart()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Chart canvas
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        
        # Button bar
        btn_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(self.edit_btn)
        
        self.add_to_cart_btn = QPushButton("Add to Cart")
        self.add_to_cart_btn.clicked.connect(self._on_add_to_cart)
        btn_layout.addWidget(self.add_to_cart_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _render_chart(self):
        """Render the chart using current config."""
        self.figure.clear()
        self.chart_controller.render(
            self.config, 
            self.figure, 
            self.app_controller.snapshot
        )
        self.canvas.draw()
    
    def _on_edit(self):
        """Open chart editor dialog."""
        # TODO: Open ChartConfigEditor dialog
        pass
    
    def _on_add_to_cart(self):
        """Add current chart to the cart."""
        self.app_controller.add_to_cart(self.config)
    
    def _on_export(self):
        """Export this single chart."""
        # TODO: File dialog + export
        pass
```

#### 3.3.2 Data Table Window

```python
# ui/data_table.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QLineEdit, 
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel
import pandas as pd

from controllers.app_controller import AppController

class DataFrameModel(QAbstractTableModel):
    """Qt model wrapper for pandas DataFrame."""
    
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df
    
    def rowCount(self, parent=None):
        return len(self._df)
    
    def columnCount(self, parent=None):
        return len(self._df.columns)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iloc[index.row(), index.column()]
            return str(value)
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(self._df.index[section])
        return None


class DataTableWindow(QDialog):
    """
    Raw DataFrame viewer with search and sort.
    
    Features:
    - View all snapshot data in tabular format
    - Search/filter by column name or value
    - Sortable columns
    - Copy selection to clipboard
    """
    
    def __init__(self, app_controller: AppController, parent=None):
        super().__init__(parent)
        self.app_controller = app_controller
        
        self.setWindowTitle("Data Table")
        self.resize(1000, 600)
        self._setup_ui()
        self._connect_signals()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter columns...")
        layout.addWidget(self.search_box)
        
        # Table view
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.table_view)
    
    def _connect_signals(self):
        self.search_box.textChanged.connect(self._on_filter_changed)
        self.app_controller.snapshot_loaded.connect(self._load_data)
    
    def _load_data(self):
        """Load DataFrame into table model."""
        if self.app_controller.snapshot is None:
            return
        
        df = self.app_controller.snapshot.snapshot
        self.model = DataFrameModel(df)
        
        # Proxy for filtering
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        self.table_view.setModel(self.proxy)
    
    def _on_filter_changed(self, text: str):
        """Filter columns by search text."""
        self.proxy.setFilterKeyColumn(-1)  # Search all columns
        self.proxy.setFilterFixedString(text)
```

#### 3.3.3 PID Info Window

```python
# ui/pid_info.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView
)
from PySide6.QtCore import Qt
from typing import Dict

from controllers.app_controller import AppController

class PidInfoWindow(QDialog):
    """
    PID metadata display window.
    
    Features:
    - Shows all PIDs with their units, min, max, descriptions
    - Searchable
    - Click to select PID in main window
    """
    
    def __init__(self, app_controller: AppController, parent=None):
        super().__init__(parent)
        self.app_controller = app_controller
        
        self.setWindowTitle("PID Information")
        self.resize(700, 500)
        self._setup_ui()
        self._connect_signals()
        self._load_pid_info()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search PIDs...")
        layout.addWidget(self.search_box)
        
        # PID table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PID Name", "Unit", "Min", "Max"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
    
    def _connect_signals(self):
        self.search_box.textChanged.connect(self._on_search)
        self.table.cellDoubleClicked.connect(self._on_pid_selected)
        self.app_controller.snapshot_loaded.connect(self._load_pid_info)
    
    def _load_pid_info(self):
        """Populate table with PID metadata."""
        if self.app_controller.snapshot is None:
            return
        
        pid_info: Dict = self.app_controller.snapshot.pid_info
        self.table.setRowCount(len(pid_info))
        
        for row, (pid_name, info) in enumerate(pid_info.items()):
            self.table.setItem(row, 0, QTableWidgetItem(pid_name))
            self.table.setItem(row, 1, QTableWidgetItem(str(info.get('unit', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(info.get('min', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(info.get('max', ''))))
    
    def _on_search(self, text: str):
        """Filter visible rows by search text."""
        text_lower = text.lower()
        for row in range(self.table.rowCount()):
            pid_name = self.table.item(row, 0).text().lower()
            self.table.setRowHidden(row, text_lower not in pid_name)
    
    def _on_pid_selected(self, row: int, column: int):
        """Notify main window to select this PID."""
        pid_name = self.table.item(row, 0).text()
        self.app_controller.select_pid(pid_name)
```

#### 3.3.4 Opening Secondary Windows from MainWindow

```python
# ui/main_window.py (additions)
from ui.chart_popup import ChartPopup
from ui.data_table import DataTableWindow
from ui.pid_info import PidInfoWindow

class MainWindow(QMainWindow):
    def __init__(self):
        # ... existing init ...
        self.data_table_window: Optional[DataTableWindow] = None
        self.pid_info_window: Optional[PidInfoWindow] = None
    
    def _setup_menus(self):
        # View menu
        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction("Data Table", self._show_data_table)
        view_menu.addAction("PID Info", self._show_pid_info)
    
    def _show_data_table(self):
        """Open or focus the data table window."""
        if self.data_table_window is None:
            self.data_table_window = DataTableWindow(self.app_controller, self)
        self.data_table_window.show()
        self.data_table_window.raise_()
    
    def _show_pid_info(self):
        """Open or focus the PID info window."""
        if self.pid_info_window is None:
            self.pid_info_window = PidInfoWindow(self.app_controller, self)
        self.pid_info_window.show()
        self.pid_info_window.raise_()
    
    def _open_chart_popup(self, config: ChartConfig):
        """Open a chart in a popup window."""
        popup = ChartPopup(self.app_controller, config, self)
        popup.show()
```

**Key Points:**
- All secondary windows receive the same `AppController` instance
- Windows connect to `snapshot_loaded` signal to refresh when data changes
- `ChartPopup` is created per-chart (multiple can be open)
- `DataTableWindow` and `PidInfoWindow` are singletons (one instance, show/hide)

**Test checkpoint:** Manual test: open each window, verify data updates when new snapshot loads.

---

### 3.4 Help Window

Split-pane help viewer: JSON-based TOC on the left, HTML content via `QTextBrowser` on the right.

```python
# ui/help_window.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTextBrowser, 
    QTreeWidget, QTreeWidgetItem, QLineEdit, QToolBar
)
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QAction
from pathlib import Path
import json

class HelpWindow(QDialog):
    """
    Split-pane help viewer.
    
    Features:
    - Left pane: Table of Contents from JSON file (tree structure)
    - Right pane: HTML content via QTextBrowser
    - Back/forward navigation
    - Search within content
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.resize(900, 650)
        self._setup_ui()
        self._load_toc()
        self._load_home()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Navigation toolbar
        toolbar = QToolBar()
        
        self.back_action = QAction("◀ Back", self)
        self.back_action.triggered.connect(self._go_back)
        toolbar.addAction(self.back_action)
        
        self.forward_action = QAction("Forward ▶", self)
        self.forward_action.triggered.connect(self._go_forward)
        toolbar.addAction(self.forward_action)
        
        toolbar.addSeparator()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setMaximumWidth(200)
        self.search_box.returnPressed.connect(self._search)
        toolbar.addWidget(self.search_box)
        
        layout.addWidget(toolbar)
        
        # Splitter: TOC on left, content on right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left pane: Table of Contents (tree)
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("Contents")
        self.toc_tree.setMinimumWidth(200)
        self.toc_tree.itemClicked.connect(self._on_toc_clicked)
        splitter.addWidget(self.toc_tree)
        
        # Right pane: HTML content
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.backwardAvailable.connect(self.back_action.setEnabled)
        self.browser.forwardAvailable.connect(self.forward_action.setEnabled)
        splitter.addWidget(self.browser)
        
        # Set splitter proportions (30% TOC, 70% content)
        splitter.setSizes([270, 630])
        layout.addWidget(splitter)
        
        # Initial button states
        self.back_action.setEnabled(False)
        self.forward_action.setEnabled(False)
    
    def _get_help_path(self) -> Path:
        """Get path to help files directory."""
        return Path(__file__).parent.parent / "help"
    
    def _load_toc(self):
        """Load table of contents from JSON file."""
        toc_path = self._get_help_path() / "toc.json"
        if not toc_path.exists():
            return
        
        with open(toc_path, 'r', encoding='utf-8') as f:
            toc_data = json.load(f)
        
        self._populate_toc(toc_data, self.toc_tree.invisibleRootItem())
    
    def _populate_toc(self, items: list, parent: QTreeWidgetItem):
        """Recursively populate TOC tree from JSON structure."""
        for item in items:
            tree_item = QTreeWidgetItem(parent)
            tree_item.setText(0, item.get('title', ''))
            tree_item.setData(0, Qt.ItemDataRole.UserRole, item.get('file', ''))
            
            # Recurse for children
            if 'children' in item:
                self._populate_toc(item['children'], tree_item)
        
        # Expand top-level items
        if parent == self.toc_tree.invisibleRootItem():
            self.toc_tree.expandAll()
    
    def _on_toc_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle TOC item click - load corresponding HTML file."""
        file_name = item.data(0, Qt.ItemDataRole.UserRole)
        if file_name:
            self._load_topic(file_name)
    
    def _load_home(self):
        """Load the default/home help page."""
        # Try to load intro or first topic
        help_path = self._get_help_path() / "index.html"
        if help_path.exists():
            self.browser.setSource(QUrl.fromLocalFile(str(help_path)))
        else:
            self.browser.setHtml("""
                <h1>Help</h1>
                <p>Select a topic from the table of contents.</p>
            """)
    
    def _load_topic(self, file_name: str):
        """Load a specific HTML help file."""
        help_path = self._get_help_path() / file_name
        if help_path.exists():
            self.browser.setSource(QUrl.fromLocalFile(str(help_path)))
    
    def _go_back(self):
        self.browser.backward()
    
    def _go_forward(self):
        self.browser.forward()
    
    def _search(self):
        """Search for text in current document."""
        text = self.search_box.text()
        if text:
            found = self.browser.find(text)
            if not found:
                # Wrap to beginning
                self.browser.moveCursor(self.browser.textCursor().Start)
                self.browser.find(text)
    
    def show_topic(self, topic: str):
        """Navigate directly to a specific help topic."""
        self._load_topic(f"{topic}.html")
        self.show()
        self.raise_()
```

#### 3.4.1 TOC JSON Format

```json
// help/toc.json
[
    {
        "title": "Getting Started",
        "file": "getting_started.html",
        "children": [
            {"title": "Installation", "file": "installation.html"},
            {"title": "First Steps", "file": "first_steps.html"}
        ]
    },
    {
        "title": "Loading Files",
        "file": "loading_files.html",
        "children": [
            {"title": "Excel Files", "file": "excel_files.html"},
            {"title": "Supported Formats", "file": "formats.html"}
        ]
    },
    {
        "title": "Charts",
        "file": "charts.html",
        "children": [
            {"title": "Quick Charts", "file": "quick_charts.html"},
            {"title": "Custom Charts", "file": "custom_charts.html"},
            {"title": "Chart Types", "file": "chart_types.html"}
        ]
    },
    {
        "title": "Exporting",
        "file": "exporting.html"
    }
]
```

#### 3.4.2 Opening Help from MainWindow

```python
# ui/main_window.py (additions)
from ui.help_window import HelpWindow

class MainWindow(QMainWindow):
    def __init__(self):
        # ... existing init ...
        self.help_window: Optional[HelpWindow] = None
    
    def _setup_menus(self):
        # Help menu
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("Help Contents", self._show_help)
        help_menu.addAction("About", self._show_about)
    
    def _show_help(self):
        """Open or focus the help window."""
        if self.help_window is None:
            self.help_window = HelpWindow(self)
        self.help_window.show()
        self.help_window.raise_()
    
    def _show_context_help(self, topic: str):
        """Open help to a specific topic (for F1 context help)."""
        if self.help_window is None:
            self.help_window = HelpWindow(self)
        self.help_window.show_topic(topic)
```

**Expected help file structure:**
```
help/
├── toc.json            # Table of contents structure
├── index.html          # Default/home page
├── getting_started.html
├── loading_files.html
├── charts.html
├── quick_charts.html
├── exporting.html
└── images/
    └── screenshot.png
```

**QTextBrowser HTML support:**
- Headings, paragraphs, lists, tables
- Links (`<a href="...">`), including anchors (`#section`)
- Images (`<img src="images/...">`)
- Inline CSS (`style="..."`)
- Basic formatting (bold, italic, code)

**Test checkpoint:** Manual test: TOC loads from JSON, clicking items loads HTML, navigation works.

---

## Implementation Order & Test Points

| Step | Deliverable | Test | Can Merge? |
|------|-------------|------|------------|
| **Phase 1** |
| 1.1 | `domain/quick_charts/definitions.py` | Unit: definitions valid | ✓ |
| 1.2 | `domain/quick_charts/builders.py` | Unit: builds ChartConfig | ✓ |
| 1.3 | `domain/chart_state.py` | Unit: reset clears state | ✓ |
| 1.4a | `domain/snapshot/header_parser.py` | Unit: parses headers | ✓ |
| 1.4b | `domain/snapshot/type_detector.py` | Unit: detects types | ✓ |
| 1.4c | `domain/snapshot/pid_extractor.py` | Unit: extracts PIDs | ✓ |
| 1.4d | `domain/snapshot/data_cleaner.py` | Unit: cleans data | ✓ |
| 1.4e | `domain/snapshot/derived_values.py` | Unit: calculates values | ✓ |
| 1.4f | `domain/snapshot/snapshot.py` | Integration: load works | ✓ |
| 1.5 | `file_io/reader_excel.py` | Unit: detects both layouts | ✓ |
| 1.6 | `rendering/base_renderer.py` | — | ✓ |
| 1.7 | `rendering/line_renderer.py` | Unit: renders to figure | ✓ |
| 1.8 | `rendering/status_renderer.py` | Unit: no state pollution | ✓ |
| 1.9 | `rendering/bar_renderer.py` | Unit: renders correctly | ✓ |
| 1.10 | `rendering/bubble_renderer.py` | Unit: renders correctly | ✓ |
| **Phase 2** |
| 2.1 | `controllers/snapshot_loader.py` | Unit: progress signals emitted | ✓ |
| 2.2 | `infrastructure/logging_config.py` | Unit: log creation, rotation, toggle | ✓ |
| 2.3 | `ui/log_console.py` | Unit: append, overwrite, colors | ✓ |
| 2.4 | `controllers/app_controller.py` | Unit: signals emitted | ✓ |
| 2.5 | `controllers/chart_controller.py` | Unit: delegates to renderer | ✓ |
| **Phase 3** |
| 3.1 | `ui/main_window.py` (skeleton) | Manual: window opens | ✓ |
| 3.2 | `ui/pid_list.py` | Manual: shows PIDs | ✓ |
| 3.3 | `ui/chart_canvas.py` | Manual: renders chart | ✓ |
| 3.4 | `ui/header_panel.py` | Manual: shows info | ✓ |
| 3.5 | `ui/axis_panel.py` | Manual: controls work | ✓ |
| 3.6 | `ui/chart_cart.py` | Manual: cart works | ✓ |
| 3.7 | `ui/log_console.py` integration | Manual: console shows logs | ✓ |
| 3.8 | `ui/chart_popup.py` | Manual: popup opens, renders | ✓ |
| 3.9 | `ui/data_table.py` | Manual: table shows data | ✓ |
| 3.10 | `ui/pid_info.py` | Manual: PID info displays | ✓ |
| 3.11 | `ui/help_window.py` | Manual: help opens, navigation works | ✓ |
| 3.12 | Full integration | E2E: load → chart → export | ✓ |

---

## Proposed File Structure

```
Snapshot-Decoder/
├── main.py                      # Entry point
├── controllers/
│   ├── __init__.py
│   ├── snapshot_loader.py       # QThread with progress signals
│   ├── app_controller.py        # Main orchestration (QObject)
│   └── chart_controller.py      # Chart rendering orchestration
├── domain/
│   ├── __init__.py
│   ├── chart_config.py          # Existing - unchanged
│   ├── chart_state.py           # NEW - explicit state management
│   ├── constants.py             # Existing
│   ├── snaptypes.py             # Existing
│   ├── snapshot/                # REFACTORED from snapshot.py
│   │   ├── __init__.py          # Exports Snapshot class
│   │   ├── snapshot.py          # Coordinator class (~80 lines)
│   │   ├── header_parser.py     # Header parsing logic
│   │   ├── type_detector.py     # Snapshot type identification
│   │   ├── pid_extractor.py     # PID metadata extraction
│   │   ├── data_cleaner.py      # DataFrame cleaning
│   │   └── derived_values.py    # Engine hours, idle time, MDP
│   └── quick_charts/
│       ├── __init__.py
│       ├── definitions.py       # Declarative chart definitions
│       ├── v1_charts.py         # V1 ECU chart definitions
│       ├── v2_charts.py         # V2 ECU chart definitions
│       ├── eud_charts.py        # EUD chart definitions
│       └── builders.py          # ChartConfig factory
├── rendering/
│   ├── __init__.py
│   ├── base_renderer.py         # Abstract base class
│   ├── line_renderer.py
│   ├── bar_renderer.py
│   ├── bubble_renderer.py
│   └── status_renderer.py
├── ui/                          # PySide6 UI
│   ├── __init__.py
│   ├── main_window.py           # QMainWindow
│   ├── header_panel.py          # File info + quick charts
│   ├── pid_list.py              # PID selection widget
│   ├── axis_panel.py            # Axis range controls
│   ├── chart_canvas.py          # Matplotlib canvas
│   ├── chart_cart.py            # Multi-chart collection
│   ├── chart_popup.py           # Enlarged chart dialog
│   ├── data_table.py            # DataFrame viewer
│   ├── pid_info.py              # PID metadata window
│   ├── help_window.py           # HTML help viewer
│   ├── log_console.py           # Live log viewer with overwrite
│   └── toolbar.py               # Navigation toolbar
├── file_io/
│   ├── __init__.py
│   ├── reader_excel.py          # UPGRADED - layout detection
│   └── pdf_export.py            # Existing
├── infrastructure/
│   ├── __init__.py
│   └── logging_config.py        # Rotating file logs, verbose toggle
└── tests/
    ├── __init__.py
    ├── test_quick_chart_definitions.py
    ├── test_chart_config_builder.py
    ├── test_chart_state.py
    ├── test_layout_detector.py
    ├── test_header_parser.py
    ├── test_type_detector.py
    ├── test_pid_extractor.py
    ├── test_data_cleaner.py
    ├── test_derived_values.py
    ├── test_snapshot_integration.py
    ├── test_snapshot_loader.py
    ├── test_logging_config.py
    ├── test_log_console.py
    ├── test_line_renderer.py
    ├── test_status_renderer.py
    ├── test_bar_renderer.py
    ├── test_bubble_renderer.py
    └── test_app_controller.py
```

---

## Dependencies Update

```txt
# requirements.txt additions for V2
PySide6>=6.4.0
matplotlib>=3.7.0  # Already present, verify Qt backend support
```

---

## Migration Notes

- **Delete after V2 complete:** `ui/app.py`, `domain/quick_charts.py` (old monolithic versions)
- **Keep unchanged:** `domain/chart_config.py`, `file_io/*`
- **Refactor:** 
  - `domain/snapshot.py` → split into `domain/snapshot/` package
  - `ui/chart_renderer.py` → split into `rendering/*`

---

## Summary

| Goal | Solution |
|------|----------|
| Better UI/logic separation | Controller layer with Qt signals |
| Fix memory issues | `ChartState` with explicit `reset()` |
| Each chart type in own file | `rendering/` folder with one class per type |
| Declarative quick charts | `QuickChartDef` dataclass, no UI refs |
| Break up snapshot.py | `domain/snapshot/` package with 6 focused modules |
| Handle both file layouts | `LayoutDetector` scans for known PIDs, transposes if needed |
| Progress feedback | `SnapshotLoader` QThread + `QProgressDialog` |
| Diagnostic logging | Rotating file logs with verbose toggle |
| Live console panel | `LogConsole` with color-coded, overwritable lines |
| Secondary windows | `ChartPopup`, `DataTableWindow`, `PidInfoWindow` share controller |
| Chain of custody | Log file path, type, hours, PIDs for each load |
| Easier maintenance | Smaller, focused files |
| Build incrementally | Phase 1 → 2 → 3, test at each step |
