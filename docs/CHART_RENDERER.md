# Chart Renderer System

## Overview

The chart rendering system has been refactored into a flexible, reusable component that can create line, bar, and bubble charts with primary and secondary axes. The system is designed to work in multiple contexts:

- **Main Window**: Embedded charts in the main application window
- **Separate Windows**: Popup windows with dedicated charts
- **PDF Export**: Charts exported to PDF documents
- **Standalone**: Independent matplotlib windows

## Architecture

### 1. `ChartConfig` (domain/chart_config.py)

A dataclass that encapsulates all parameters needed to create a chart. This separates the chart configuration from the rendering logic.

**Key Components:**
- `AxisConfig`: Configuration for primary and secondary axes
- `SeriesStyle`: Styling options for individual data series
- `ChartConfig`: Main configuration dataclass

**Example:**
```python
from domain.chart_config import ChartConfig, AxisConfig, SeriesStyle

config = ChartConfig(
    data=my_dataframe,
    chart_type="line",  # "line", "bar", or "bubble"
    primary_axis=AxisConfig(
        series=['Temperature', 'Humidity'],
        label='Environmental Metrics',
        min_value=0,
        max_value=100,
        auto_scale=False
    ),
    secondary_axis=AxisConfig(
        series=['Pressure'],
        label='Pressure (kPa)',
        auto_scale=True
    ),
    title="Multi-Axis Chart",
    x_column='Time',
    grid=True,
    series_styles={
        'Temperature': SeriesStyle(color='red', linewidth=2),
        'Pressure': SeriesStyle(linestyle='--', color='blue')
    }
)
```

### 2. `ChartRenderer` (ui/chart_renderer.py)

A class that takes a `ChartConfig` and renders the chart on a matplotlib figure.

**Key Methods:**
- `render(figure, canvas, clear_figure)`: Render on an existing figure
- `create_and_render(figsize, dpi)`: Create a new figure and render

**Example:**
```python
from ui.chart_renderer import ChartRenderer

# Render on existing figure (e.g., in tkinter)
renderer = ChartRenderer(config)
ax_left, ax_right = renderer.render(figure, canvas)

# Create new figure
fig, ax_left, ax_right = renderer.create_and_render(figsize=(10, 6))
```

## Chart Types

### Line Chart
Best for showing trends over time or continuous data.

```python
config = ChartConfig(
    data=df,
    chart_type="line",
    primary_axis=AxisConfig(series=['Series1', 'Series2']),
    ...
)
```

### Bar Chart
Best for comparing discrete values or categories.

```python
config = ChartConfig(
    data=df,
    chart_type="bar",
    primary_axis=AxisConfig(series=['Series1']),
    secondary_axis=AxisConfig(series=['Series2']),
    ...
)
```

### Bubble Chart
Scatter plot useful for showing relationships or distributions.

```python
config = ChartConfig(
    data=df,
    chart_type="bubble",
    series_styles={
        'Series1': SeriesStyle(markersize=10, alpha=0.6),
        'Series2': SeriesStyle(markersize=8, alpha=0.5)
    },
    ...
)
```

## Usage in Different Contexts

### 1. Main Window (Current Implementation)

In `app.py`, the `plot_combo_chart` method now uses `ChartRenderer`:

```python
def plot_combo_chart(self):
    # Create configuration
    config = ChartConfig(
        data=self.snapshot.copy(),
        chart_type="line",
        primary_axis=AxisConfig(
            series=list(self.primary_series),
            auto_scale=self.primary_auto.get(),
            ...
        ),
        ...
    )
    
    # Render
    renderer = ChartRenderer(config)
    self.ax_left, self.ax_right = renderer.render(self.figure, self.canvas)
```

### 2. Separate Window

Create a popup window with its own chart:

```python
def show_chart_window(self):
    # Create new window
    window = tk.Toplevel(self)
    window.title("Chart Window")
    
    # Create figure and canvas
    figure = Figure(figsize=(8, 6))
    canvas = FigureCanvasTkAgg(figure, window)
    canvas.get_tk_widget().pack()
    
    # Configure and render
    config = ChartConfig(data=self.data, ...)
    renderer = ChartRenderer(config)
    renderer.render(figure, canvas)
```

### 3. PDF Export

Export charts to a PDF file:

```python
from matplotlib.backends.backend_pdf import PdfPages

def export_to_pdf(self, filename):
    with PdfPages(filename) as pdf:
        config = ChartConfig(data=self.data, ...)
        renderer = ChartRenderer(config)
        fig, _, _ = renderer.create_and_render(figsize=(8.5, 11))
        pdf.savefig(fig)
        plt.close(fig)
```

### 4. Standalone Matplotlib

Create an independent matplotlib window:

```python
def show_standalone_chart(data):
    config = ChartConfig(data=data, ...)
    renderer = ChartRenderer(config)
    fig, _, _ = renderer.create_and_render()
    plt.show()
```

## Advanced Features

### Custom Series Styling

Customize individual series appearance:

```python
config = ChartConfig(
    data=df,
    series_styles={
        'Series1': SeriesStyle(
            linestyle='-',
            linewidth=2,
            color='red',
            marker='o',
            markersize=6,
            alpha=0.8
        ),
        'Series2': SeriesStyle(
            linestyle='--',
            linewidth=1.5,
            color='blue'
        )
    }
)
```

### Axis Limits

Control axis scaling:

```python
primary_axis = AxisConfig(
    series=['Temperature'],
    min_value=0,      # Set minimum
    max_value=100,    # Set maximum
    auto_scale=False  # Disable auto-scaling
)
```

### Auto-Detecting Units

The system can automatically detect units from PID information:

```python
config = ChartConfig(
    data=df,
    pid_info={
        'Temperature': {'Unit': '°C'},
        'Pressure': {'Unit': 'kPa'}
    },
    primary_axis=AxisConfig(series=['Temperature']),
    # Label will automatically be set to '°C'
)
```

## Migration Guide

### Old Code
```python
def plot_combo_chart(self):
    self.figure.clear()
    self.ax_left = self.figure.add_subplot(111)
    self.ax_right = self.ax_left.twinx()
    
    for s in self.primary_series:
        self.ax_left.plot(df[x_key], df[s], label=s)
    
    # ... lots of manual plotting code
    self.canvas.draw_idle()
```

### New Code
```python
def plot_combo_chart(self):
    config = ChartConfig(
        data=self.snapshot.copy(),
        chart_type="line",
        primary_axis=AxisConfig(series=list(self.primary_series)),
        secondary_axis=AxisConfig(series=list(self.secondary_series))
    )
    
    renderer = ChartRenderer(config)
    self.ax_left, self.ax_right = renderer.render(self.figure, self.canvas)
```

## Benefits

1. **Separation of Concerns**: Configuration is separate from rendering logic
2. **Reusability**: Same code works in different contexts
3. **Testability**: Easy to unit test with mock data
4. **Extensibility**: Easy to add new chart types
5. **Maintainability**: Centralized chart rendering logic
6. **Type Safety**: Dataclasses provide type hints and validation

## Examples

See `examples/chart_renderer_usage.py` for complete working examples of all use cases.

## Future Enhancements

Potential additions to the system:
- Additional chart types (area, scatter with regression, etc.)
- Animation support for time-series data
- Interactive features (zoom, pan, tooltips)
- Theme support (dark mode, custom color schemes)
- Export to other formats (SVG, PNG)
- Multi-page PDF reports with multiple charts
