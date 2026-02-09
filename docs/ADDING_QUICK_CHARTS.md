# Adding Quick Charts to Snapshot Decoder

This guide walks through how to add a new quick chart to the application. Quick charts are pre-configured chart definitions that appear as buttons in the UI when a matching snapshot type is loaded.

---

## Architecture Overview

The quick chart system has four layers:

| Layer | File(s) | Purpose |
|-------|---------|---------|
| **Definitions** | `domain/quick_charts/definitions.py` | Dataclasses that describe chart structure |
| **Chart files** | `domain/quick_charts/v1_charts.py`, `v2_charts.py`, `eud_charts.py` | Instances of definitions grouped by snapshot type |
| **Registry** | `domain/quick_charts/__init__.py` | Combines all chart dicts into `QUICK_CHART_REGISTRY` |
| **Button config** | `domain/constants.py` | Maps `SnapType` → list of UI button tuples |

### Data flow when a user clicks a quick chart button

```
QuickChartPanel (button click)
  → emits chart_requested signal with action_id string
  → MainWindow._on_quick_chart_requested(action_id)
  → ChartWidget.plot_quick_chart(snapshot, action_id)
      → looks up action_id in QUICK_CHART_REGISTRY
      → ChartConfigBuilder.build(definition, snapshot) → ChartConfig
      → ChartRenderer(config).render(figure, canvas)
```

---

## Step-by-Step: Adding a New Quick Chart

### 1. Choose the correct definition type

Open `domain/quick_charts/definitions.py` and pick the dataclass that matches your chart:

| Type | Class | Use when |
|------|-------|----------|
| Line chart | `QuickChartDef` | Plotting one or more PIDs over time (frames) |
| Status chart | `StatusChartDef` | Showing binary on/off or categorical states over time |
| Bar chart | `BarChartDef` | Showing single-value comparisons (e.g. hours at speed band) |
| Bubble chart | `BubbleChartDef` | Showing 3-variable relationships (x, y, size) |

### 2. Create the definition instance

Open the chart file for the target snapshot type:

- **V1 ECU** → `domain/quick_charts/v1_charts.py`
- **V2 ECU** → `domain/quick_charts/v2_charts.py`
- **EUD** → `domain/quick_charts/eud_charts.py`

Add your definition. Here are examples for each type:

#### Line chart

```python
V2_MY_NEW_CHART = QuickChartDef(
    action_id="V2_MY_NEW_CHART",
    title="My New Chart Title",
    primary_pids=["SomePid_value", "AnotherPid_value"],
    primary_range=(0, 100),          # Optional fixed Y-axis range; omit for auto-scale
    secondary_pids=["ThirdPid_rpm"], # Optional right-side Y-axis PIDs
    secondary_range=(0, 3000),       # Optional fixed range for secondary axis
)
```

#### Status chart

```python
V2_MY_STATUS = StatusChartDef(
    action_id="V2_MY_STATUS",
    title="System Status Flags",
    primary_pids=["Flag_A", "Flag_B", "Flag_C"],
    chart_type="status",
    show_legend=True,
)
```

#### Parsed status chart (multi-digit column)

```python
V2_PARSED_STATUS = StatusChartDef(
    action_id="V2_PARSED_STATUS",
    title="Decoded Status Bits",
    primary_pids=[],                          # Left empty; PIDs generated from digits
    chart_type="status",
    source_column="SomeStatus_stColumn",      # Column containing digit strings like "00101"
    digit_labels=["Bit 0 Name", "Bit 1 Name", "Bit 2 Name"],
    display_prefix="Status:",                 # Optional prefix for generated PID names
)
```

#### Bar chart

```python
V1EUD_MY_BAR = BarChartDef(
    action_id="V1EUD_MY_BAR",
    title="Hours by Category",
    primary_pids=[],                          # Left empty for bar charts
    chart_type="bar",
    source_columns=[                          # Column names to pull Frame 0 values from
        "EUD_some_timer_nvv[0]",
        "EUD_some_timer_nvv[1]",
        "EUD_some_timer_nvv[2]",
    ],
    bar_labels=["Low", "Medium", "High"],     # Must match length of source_columns
    x_label="Category",
    y_label="Hours",
    convert_seconds_to_hours=True,            # Divides raw seconds by 3600
)
```

#### Bubble chart

```python
V1EUD_MY_BUBBLE = BubbleChartDef(
    action_id="V1EUD_MY_BUBBLE",
    title="Speed vs Load Distribution",
    primary_pids=[],
    chart_type="bubble",
    column_pattern="EUD_Spdload_blm_timer_nvv[{x},{y}]",
    total_reference_column="EUD_Engine_run_time_total_nvv",
    x_label="Engine Speed (RPM)",
    y_label="Load (%)",
    size_label="% of Run Time",
    x_index_map={i: 900 + (i * 200) for i in range(16)},
    y_index_map={i: 5 + (i * 10) for i in range(11)},
)
```

### 3. Register the definition in the chart file's dictionary

At the bottom of the same file, add your new chart to the registry dict:

```python
V2_CHARTS: dict[str, QuickChartDef] = {
    # ... existing entries ...
    "V2_MY_NEW_CHART": V2_MY_NEW_CHART,    # My New Chart
}
```

> The key **must** match the `action_id` string exactly.

### 4. Add a UI button in `domain/constants.py`

Find the `BUTTONS_BY_TYPE` dict and add a tuple under the correct `SnapType`:

```python
BUTTONS_BY_TYPE: dict[SnapType, list[tuple[str, str, str]]] = {
    SnapType.ECU_V2: [
        # ... existing buttons ...
        ("My Chart", "V2_MY_NEW_CHART", "Tooltip description for the button"),
    ],
}
```

The tuple format is: `(button_label, action_id, tooltip_text)`

### 5. Verify

1. Run the application: `python main.py`
2. Load a snapshot file that matches your target `SnapType`
3. The new button should appear in the **Quick Charts** panel
4. Click the button — the chart should render

---

## Key Fields Reference

### QuickChartDef fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_id` | `str` | Yes | Unique identifier, must match registry key and button config |
| `title` | `str` | Yes | Chart title displayed above the plot |
| `primary_pids` | `list[str]` | Yes | PID column names for the left Y-axis |
| `primary_range` | `tuple[float, float]` | No | Fixed min/max for left Y-axis; omit for auto-scale |
| `secondary_pids` | `list[str]` | No | PID column names for the right Y-axis |
| `secondary_range` | `tuple[float, float]` | No | Fixed min/max for right Y-axis |
| `chart_type` | `str` | No | `"line"` (default), `"status"`, `"bar"`, or `"bubble"` |
| `show_legend` | `bool` | No | Show legend (default `True`) |
| `dynamic_primary_pids` | `list[str]` | No | Superset of PIDs filtered to those present in data (e.g. 3 vs 4 cylinder) |

### Naming convention for action_id

- V1 ECU charts: `V1_CHART_NAME`
- V2 ECU charts: `V2_CHART_NAME`
- EUD charts: `V1EUD_CHART_NAME`
- Reference charts: `REF_CHART_NAME`

---

## Tips

- **PID names must match the snapshot column headers exactly** (case-sensitive). Open a snapshot file to verify column names.
- **Auto-scale vs fixed range**: Omit `primary_range`/`secondary_range` to let matplotlib auto-scale. Use fixed ranges when you want consistent Y-axis limits across different snapshot files.
- **Dynamic PIDs**: Use `dynamic_primary_pids` when the number of PIDs varies (e.g. 3-cylinder vs 4-cylinder engines have different numbers of piston delta PIDs).
- **The builder filters out missing PIDs automatically** — if a PID in your definition doesn't exist in the loaded snapshot, it is silently skipped.
- **No UI code needed**: The `QuickChartPanel` reads from `BUTTONS_BY_TYPE` and the `ChartConfigBuilder` reads from the registry. You only touch domain-layer files.
