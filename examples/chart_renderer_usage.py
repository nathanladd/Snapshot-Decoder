"""
Example Usage of ChartRenderer

This file demonstrates how to use the ChartRenderer class in different contexts:
1. Embedded in a tkinter window
2. Standalone matplotlib window
3. PDF export
"""

import pandas as pd
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from domain.chart_config import ChartConfig, AxisConfig, SeriesStyle
from ui.chart_renderer import ChartRenderer


# Sample data
def create_sample_data():
    """Create sample data for demonstration."""
    return pd.DataFrame({
        'Time': range(100),
        'Temperature': [20 + i * 0.1 + (i % 10) for i in range(100)],
        'Pressure': [100 + i * 0.5 - (i % 5) * 2 for i in range(100)],
        'Flow': [50 + (i % 20) * 1.5 for i in range(100)]
    })


# Example 1: Embedded in tkinter window (like the main app)
def example_tkinter_embedded():
    """Example of using ChartRenderer embedded in a tkinter window."""
    
    # Create tkinter window
    root = tk.Tk()
    root.title("ChartRenderer - Tkinter Example")
    root.geometry("800x600")
    
    # Create matplotlib figure and canvas
    figure = Figure(figsize=(8, 6), dpi=100)
    canvas = FigureCanvasTkAgg(figure, root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Create chart configuration
    config = ChartConfig(
        data=create_sample_data(),
        chart_type="line",
        primary_axis=AxisConfig(
            series=['Temperature'],
            label='Temperature (°C)'
        ),
        secondary_axis=AxisConfig(
            series=['Pressure', 'Flow'],
            label='Pressure (kPa) / Flow (L/min)'
        ),
        title="Multi-Axis Line Chart",
        x_column='Time',
        x_label='Time (s)'
    )
    
    # Render the chart
    renderer = ChartRenderer(config)
    renderer.render(figure, canvas)
    
    # Button to switch to bar chart
    def switch_to_bar():
        config.chart_type = "bar"
        renderer.render(figure, canvas)
    
    # Button to switch to bubble chart
    def switch_to_bubble():
        config.chart_type = "bubble"
        # Increase marker size for bubble chart
        config.series_styles = {
            'Temperature': SeriesStyle(markersize=10),
            'Pressure': SeriesStyle(markersize=8),
            'Flow': SeriesStyle(markersize=12)
        }
        renderer.render(figure, canvas)
    
    # Add control buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
    
    ttk.Button(button_frame, text="Line Chart", 
               command=lambda: setattr(config, 'chart_type', 'line') or renderer.render(figure, canvas)
    ).pack(side=tk.LEFT, padx=2)
    
    ttk.Button(button_frame, text="Bar Chart", command=switch_to_bar).pack(side=tk.LEFT, padx=2)
    ttk.Button(button_frame, text="Bubble Chart", command=switch_to_bubble).pack(side=tk.LEFT, padx=2)
    
    root.mainloop()


# Example 2: Standalone matplotlib window
def example_standalone_window():
    """Example of using ChartRenderer with standalone matplotlib."""
    
    # Create chart configuration
    config = ChartConfig(
        data=create_sample_data(),
        chart_type="line",
        primary_axis=AxisConfig(
            series=['Temperature'],
            label='Temperature (°C)',
            min_value=15,
            max_value=35,
            auto_scale=False
        ),
        secondary_axis=AxisConfig(
            series=['Pressure'],
            label='Pressure (kPa)'
        ),
        title="Standalone Chart with Custom Limits",
        x_column='Time',
        x_label='Time (s)'
    )
    
    # Create and render
    renderer = ChartRenderer(config)
    fig, ax_left, ax_right = renderer.create_and_render(figsize=(10, 6))
    
    # Show the plot
    plt.show()


# Example 3: Export to PDF
def example_pdf_export(filename='chart_export.pdf'):
    """Example of using ChartRenderer to export to PDF."""
    from matplotlib.backends.backend_pdf import PdfPages
    
    data = create_sample_data()
    
    # Create multiple charts in one PDF
    with PdfPages(filename) as pdf:
        # Chart 1: Line chart
        config1 = ChartConfig(
            data=data,
            chart_type="line",
            primary_axis=AxisConfig(series=['Temperature']),
            secondary_axis=AxisConfig(series=['Pressure']),
            title="Line Chart - Temperature vs Pressure"
        )
        renderer1 = ChartRenderer(config1)
        fig1, _, _ = renderer1.create_and_render(figsize=(8.5, 11))
        pdf.savefig(fig1)
        plt.close(fig1)
        
        # Chart 2: Bar chart
        config2 = ChartConfig(
            data=data.iloc[::5],  # Sample every 5th point for readability
            chart_type="bar",
            primary_axis=AxisConfig(series=['Temperature', 'Flow']),
            title="Bar Chart - Temperature and Flow"
        )
        renderer2 = ChartRenderer(config2)
        fig2, _, _ = renderer2.create_and_render(figsize=(8.5, 11))
        pdf.savefig(fig2)
        plt.close(fig2)
        
        # Chart 3: Bubble chart
        config3 = ChartConfig(
            data=data.iloc[::2],  # Sample every 2nd point
            chart_type="bubble",
            primary_axis=AxisConfig(series=['Pressure']),
            secondary_axis=AxisConfig(series=['Flow']),
            title="Bubble Chart - Pressure vs Flow",
            series_styles={
                'Pressure': SeriesStyle(markersize=10, alpha=0.6),
                'Flow': SeriesStyle(markersize=8, alpha=0.6)
            }
        )
        renderer3 = ChartRenderer(config3)
        fig3, _, _ = renderer3.create_and_render(figsize=(8.5, 11))
        pdf.savefig(fig3)
        plt.close(fig3)
    
    print(f"PDF exported to: {filename}")


# Example 4: Using in a separate window (like a popup)
def example_separate_window():
    """Example of creating a chart in a separate tkinter window."""
    
    # Create a separate window
    window = tk.Toplevel()
    window.title("Separate Chart Window")
    window.geometry("700x500")
    
    # Create matplotlib figure and canvas
    figure = Figure(figsize=(7, 5), dpi=100)
    canvas = FigureCanvasTkAgg(figure, window)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Configure with custom styling
    config = ChartConfig(
        data=create_sample_data(),
        chart_type="line",
        primary_axis=AxisConfig(series=['Temperature', 'Flow']),
        title="Chart in Separate Window",
        series_styles={
            'Temperature': SeriesStyle(color='red', linewidth=2),
            'Flow': SeriesStyle(color='blue', linewidth=2, linestyle='--')
        }
    )
    
    # Render
    renderer = ChartRenderer(config)
    renderer.render(figure, canvas)
    
    # Add close button
    ttk.Button(window, text="Close", command=window.destroy).pack(pady=5)


def main():
    """Main function to demonstrate usage."""
    import sys
    
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
    else:
        print("Usage examples:")
        print("  python chart_renderer_usage.py tkinter    - Tkinter embedded example")
        print("  python chart_renderer_usage.py standalone - Standalone matplotlib window")
        print("  python chart_renderer_usage.py pdf        - Export to PDF")
        print("  python chart_renderer_usage.py popup      - Separate window example")
        return
    
    if example_type == "tkinter":
        example_tkinter_embedded()
    elif example_type == "standalone":
        example_standalone_window()
    elif example_type == "pdf":
        example_pdf_export()
    elif example_type == "popup":
        root = tk.Tk()
        root.withdraw()  # Hide main window
        example_separate_window()
        root.mainloop()
    else:
        print(f"Unknown example type: {example_type}")


if __name__ == "__main__":
    main()
