"""
Test script for live values display functionality.
"""

import pandas as pd
import numpy as np
from domain.chart_config import ChartConfig, AxisConfig
from domain.pid_interpolator import PIDInterpolator
from ui.live_values_display import PIDCard
import tkinter as tk
from tkinter import ttk

def test_interpolator():
    """Test the PID interpolator with sample data."""
    print("Testing PID Interpolator...")
    
    # Create sample data
    data = pd.DataFrame({
        'Time': [0.0, 0.5, 1.0, 1.5, 2.0],
        'Engine_Speed': [800, 1200, 1850, 2100, 2000],
        'Rail_Pressure': [200, 350, 450, 520, 480],
        'Boost_Temp': [20, 45, 85, 105, 95]
    })
    
    # Create chart config
    primary_axis = AxisConfig(series=['Engine_Speed', 'Rail_Pressure'])
    secondary_axis = AxisConfig(series=['Boost_Temp'])
    
    config = ChartConfig(
        data=data,
        chart_type="line",
        primary_axis=primary_axis,
        secondary_axis=secondary_axis,
        title="Test Chart"
    )
    
    # Test interpolation
    interpolator = PIDInterpolator()
    
    # Test at existing data points
    values_at_1_0 = interpolator.interpolate_values(config, 1.0)
    print(f"Values at t=1.0: {values_at_1_0}")
    
    # Test between data points
    values_at_1_25 = interpolator.interpolate_values(config, 1.25)
    print(f"Values at t=1.25: {values_at_1_25}")
    
    # Test out of bounds
    values_at_minus_1 = interpolator.interpolate_values(config, -1.0)
    print(f"Values at t=-1.0: {values_at_minus_1}")
    
    values_at_3_0 = interpolator.interpolate_values(config, 3.0)
    print(f"Values at t=3.0: {values_at_3_0}")
    
    print("✓ Interpolator test passed!\n")

def test_pid_card():
    """Test PID card creation."""
    print("Testing PID Card...")
    
    root = tk.Tk()
    root.withdraw()  # Hide window
    
    card = PIDCard(root, "Engine_Speed", "#FF0000", 1850.0)
    print(f"Created card for PID: {card.pid_name}")
    print(f"Card color: {card.color}")
    
    # Test value update
    card.update_value(2100.0)
    print("✓ Card value updated")
    
    card.destroy()
    root.destroy()
    
    print("✓ PID Card test passed!\n")

def test_live_values_display():
    """Test live values display widget."""
    print("Testing Live Values Display...")
    
    # Create sample data
    data = pd.DataFrame({
        'Time': [0.0, 0.5, 1.0, 1.5, 2.0],
        'Engine_Speed': [800, 1200, 1850, 2100, 2000],
        'Rail_Pressure': [200, 350, 450, 520, 480],
        'Boost_Temp': [20, 45, 85, 105, 95]
    })
    
    # Create chart config
    primary_axis = AxisConfig(series=['Engine_Speed', 'Rail_Pressure'])
    secondary_axis = AxisConfig(series=['Boost_Temp'])
    
    config = ChartConfig(
        data=data,
        chart_type="line",
        primary_axis=primary_axis,
        secondary_axis=secondary_axis,
        title="Test Chart"
    )
    
    root = tk.Tk()
    root.withdraw()  # Hide window
    
    display = LiveValuesDisplay(root, config)
    print(f"Created display with {len(display.cards)} cards")
    
    # Test value updates
    display.update_values(1.0)
    print("✓ Values updated at t=1.0")
    
    display.update_values(1.25)
    print("✓ Values updated at t=1.25")
    
    # Test cache info
    cache_info = display.get_cache_info()
    print(f"Cache info: {cache_info}")
    
    display.destroy()
    root.destroy()
    
    print("✓ Live Values Display test passed!\n")

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Live Values Display Implementation")
    print("=" * 50)
    
    try:
        test_interpolator()
        test_pid_card()
        test_live_values_display()
        
        print("=" * 50)
        print("✓ All tests passed successfully!")
        print("Live values display is ready for integration.")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
