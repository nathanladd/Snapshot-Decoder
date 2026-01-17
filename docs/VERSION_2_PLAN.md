# Version 2 Planning Document

> **Target:** PyQt6-only UI with clean architecture separation  
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

## V2 Architecture (PyQt6-Only)

### Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (PyQt6)                     │
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

class DerivedValues:
    """Calculates derived values from snapshot data."""
    
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
from domain.snapshot.derived_values import DerivedValues
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
        
        self.hours = DerivedValues.find_engine_hours(self.snapshot, self.snapshot_type, self.pid_info)
        self.idle_time = DerivedValues.find_idle_time(self.snapshot, self.pid_info)
        self.mdp_success_rate = DerivedValues.calculate_mdp_success(self.snapshot)
        
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

### 2.1 AppController

```python
# controllers/app_controller.py
from PyQt6.QtCore import QObject, pyqtSignal
from domain.snapshot import Snapshot
from domain.chart_state import ChartState
from domain.quick_charts.definitions import QUICK_CHART_REGISTRY
from domain.quick_charts.builders import ChartConfigBuilder

class AppController(QObject):
    """Main application controller - orchestrates all app actions."""
    
    # Signals for UI to connect to
    snapshot_loaded = pyqtSignal(object)  # emits Snapshot
    chart_updated = pyqtSignal(object)    # emits ChartConfig
    error_occurred = pyqtSignal(str)      # emits error message
    
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

## Phase 3: UI Layer (PyQt6)

**Goal:** Build PyQt6 UI that connects to controllers via signals/slots.

### 3.1 Main Window Structure

```python
# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
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
| 2.1 | `controllers/app_controller.py` | Unit: signals emitted | ✓ |
| 2.2 | `controllers/chart_controller.py` | Unit: delegates to renderer | ✓ |
| **Phase 3** |
| 3.1 | `ui/main_window.py` (skeleton) | Manual: window opens | ✓ |
| 3.2 | `ui/pid_list.py` | Manual: shows PIDs | ✓ |
| 3.3 | `ui/chart_canvas.py` | Manual: renders chart | ✓ |
| 3.4 | `ui/header_panel.py` | Manual: shows info | ✓ |
| 3.5 | `ui/axis_panel.py` | Manual: controls work | ✓ |
| 3.6 | `ui/chart_cart.py` | Manual: cart works | ✓ |
| 3.7 | Full integration | E2E: load → chart → export | ✓ |

---

## Proposed File Structure

```
Snapshot-Decoder/
├── main.py                      # Entry point
├── controllers/
│   ├── __init__.py
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
├── ui/                          # PyQt6 UI
│   ├── __init__.py
│   ├── main_window.py           # QMainWindow
│   ├── header_panel.py          # File info + quick charts
│   ├── pid_list.py              # PID selection widget
│   ├── axis_panel.py            # Axis range controls
│   ├── chart_canvas.py          # Matplotlib canvas
│   ├── chart_cart.py            # Multi-chart collection
│   └── toolbar.py               # Navigation toolbar
├── file_io/
│   ├── __init__.py
│   ├── reader_excel.py          # UPGRADED - layout detection
│   └── pdf_export.py            # Existing
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
PyQt6>=6.4.0
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
| Easier maintenance | Smaller, focused files |
| Build incrementally | Phase 1 → 2 → 3, test at each step |
