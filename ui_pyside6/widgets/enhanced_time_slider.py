"""
Enhanced Time Slider Widget

Simple enhancement functions for matplotlib Slider to improve visual appearance
and add time display functionality.
"""

import numpy as np
import matplotlib.text as mtext


def enhance_slider(slider, show_time_display=True):
    """
    Enhance an existing matplotlib Slider with better visual appearance and time display.
    
    Args:
        slider: Existing matplotlib Slider instance
        show_time_display: Whether to add time display functionality
        
    Returns:
        Enhanced slider with additional attributes for time display
    """
    # Enhanced features
    slider._time_display = None
    slider._is_dragging = False
    slider._show_time_display = show_time_display
    
    # Customize appearance (this always works)
    _enhance_slider_appearance(slider)
    
    # Only connect events if time display is requested
    if show_time_display:
        try:
            _connect_enhanced_events(slider)
        except Exception as e:
            print(f"Warning: Could not connect enhanced slider events: {e}")
            # Continue without time display, but keep visual enhancements
    
    return slider


def _enhance_slider_appearance(slider):
    """Enhance the visual appearance of the slider."""
    # Make the handle more prominent
    if hasattr(slider, 'poly'):
        # Customize the handle (matplotlib creates this as a polygon)
        slider.poly.set_facecolor('red')
        slider.poly.set_edgecolor('darkred')
        slider.poly.set_linewidth(4)  # Even thicker border for visibility
        slider.poly.set_alpha(1.0)    # Fully opaque for visibility
        
        # Try to make the handle much larger by modifying its vertices
        try:
            # Get current vertices and scale them aggressively
            verts = slider.poly.get_xy()
            if len(verts) > 0:
                # Scale the handle to be much larger (wider and taller)
                center_x = np.mean(verts[:, 0])
                center_y = np.mean(verts[:, 1])
                width = verts[:, 0].max() - verts[:, 0].min()
                height = verts[:, 1].max() - verts[:, 1].min()
                new_width = width * 3.0  # 200% wider (much more aggressive)
                new_height = height * 2.5  # 150% taller (much more aggressive)
                
                # Recreate vertices with increased size
                new_verts = [
                    [center_x - new_width/2, center_y - new_height/2],
                    [center_x + new_width/2, center_y - new_height/2],
                    [center_x + new_width/2, center_y + new_height/2],
                    [center_x - new_width/2, center_y + new_height/2]
                ]
                slider.poly.set_xy(new_verts)
                
                # Also try to make it stand out more with z-order
                slider.poly.set_zorder(10)
                
        except Exception as e:
            # If modifying vertices fails, just keep the enhanced colors
            print(f"Note: Could not resize handle: {e}")
            pass
    
    # Enhance track appearance to make handle more visible
    if hasattr(slider, 'ax'):
        slider.ax.set_facecolor('#f8f8f8')  # Light gray background
        # Remove axis spines for cleaner look
        for spine in slider.ax.spines.values():
            spine.set_visible(False)
        slider.ax.tick_params(left=False, right=False, top=False, bottom=False)
        slider.ax.set_xticks([])
        slider.ax.set_yticks([])
        
        # Try to enhance the track color manually to create contrast
        try:
            # The track is typically a rectangle in the slider
            for child in slider.ax.get_children():
                if hasattr(child, 'set_facecolor') and child != slider.poly:
                    # This might be the track - make it lighter for contrast
                    child.set_facecolor('#e0e0e0')  # Lighter gray track
                    child.set_alpha(0.6)
                    break
        except Exception:
            pass  # If track enhancement fails, continue with other enhancements


def _connect_enhanced_events(slider):
    """Connect enhanced mouse events for better interaction."""
    try:
        # Simple approach: just add our handler without touching existing ones
        def enhanced_handler(val):
            # Update time display if dragging
            if slider._is_dragging:
                _update_time_display(slider, val)
        
        # Add our enhanced handler (this will coexist with existing handlers)
        slider.on_changed(enhanced_handler)
        
        # Connect mouse events for drag detection
        slider.connect_event('button_press_event', lambda e: _on_mouse_press(slider, e))
        slider.connect_event('button_release_event', lambda e: _on_mouse_release(slider, e))
        slider.connect_event('motion_notify_event', lambda e: _on_mouse_motion(slider, e))
        
    except Exception as e:
        # If event connection fails, continue without enhanced features
        print(f"Warning: Could not connect enhanced slider events: {e}")
        pass


def _on_mouse_press(slider, event):
    """Handle mouse press event."""
    if event.inaxes == slider.ax:
        slider._is_dragging = True
        _show_time_display(slider)


def _on_mouse_release(slider, event):
    """Handle mouse release event."""
    slider._is_dragging = False
    _hide_time_display(slider)


def _on_mouse_motion(slider, event):
    """Handle mouse motion event."""
    if slider._is_dragging and event.inaxes == slider.ax:
        _update_time_display_position(slider)


def _show_time_display(slider):
    """Show the time display near the handle."""
    if slider._time_display is None:
        # Create text display
        slider._time_display = slider.ax.text(
            0, 0, '',  # Position will be updated
            ha='center', va='bottom',
            fontsize=11, fontweight='bold',
            color='darkred',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='red', alpha=0.95)
            )
    
    slider._time_display.set_visible(True)
    _update_time_display(slider, slider.val)


def _hide_time_display(slider):
    """Hide the time display."""
    if slider._time_display:
        slider._time_display.set_visible(False)
        # Try to redraw canvas
        try:
            if hasattr(slider, 'ax') and slider.ax and hasattr(slider.ax, 'figure') and slider.ax.figure:
                slider.ax.figure.canvas.draw_idle()
        except Exception:
            pass


def _update_time_display(slider, val=None):
    """Update the time display value and position."""
    if slider._time_display is None:
        return
    
    val = val if val is not None else slider.val
    
    # Format the value
    if abs(val) < 1:
        text = f'{val:.3f}'
    elif abs(val) < 100:
        text = f'{val:.2f}'
    else:
        text = f'{val:.1f}'
    
    # Add units if it looks like time
    if val > 0 and val < 1000:
        text += 's'
    
    slider._time_display.set_text(text)
    
    # Position the text above the handle
    handle_x = slider.val  # Handle is at current value
    
    # Convert to display coordinates (position above slider)
    display_x = handle_x
    display_y = 1.3  # Position above the slider
    
    slider._time_display.set_position((display_x, display_y))
    
    # Redraw canvas with error handling
    try:
        if (hasattr(slider, 'ax') and slider.ax and 
            hasattr(slider.ax, 'figure') and slider.ax.figure):
            slider.ax.figure.canvas.draw_idle()
    except Exception:
        pass  # If canvas update fails, continue without crashing


def _update_time_display_position(slider):
    """Update only the position of the time display."""
    if slider._time_display:
        handle_x = slider.val
        display_y = 1.3  # Position above the slider
        slider._time_display.set_position((handle_x, display_y))
        
        # Redraw canvas with error handling
        try:
            if (hasattr(slider, 'ax') and slider.ax and 
                hasattr(slider.ax, 'figure') and slider.ax.figure):
                slider.ax.figure.canvas.draw_idle()
        except Exception:
            pass


# Backward compatibility class
class EnhancedTimeSlider:
    """Backward compatibility class that uses the enhancement functions."""
    
    def __init__(self, ax, label, valmin, valmax, valinit=None, valfmt=None, **kwargs):
        """Create enhanced slider by enhancing a standard matplotlib Slider."""
        from matplotlib.widgets import Slider
        
        # Remove unsupported parameters
        unsupported_params = ['handlestyle', 'trackcolor', 'hovercolor', 'activecolor']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in unsupported_params}
        
        # Set defaults
        defaults = {
            'color': 'lightgray',
            'valmin': valmin,
            'valmax': valmax,
            'valinit': valinit if valinit is not None else valmin,
            'valfmt': valfmt if valfmt is not None else '%.2f'
        }
        defaults.update(filtered_kwargs)
        
        # Create standard slider
        self._slider = Slider(ax, label, **defaults)
        
        # Enhance it
        enhance_slider(self._slider, show_time_display=True)
    
    # Delegate all methods to the wrapped slider
    def __getattr__(self, name):
        """Delegate attribute access to the wrapped slider."""
        return getattr(self._slider, name)
    
    @property
    def val(self):
        """Get the current slider value."""
        return self._slider.val
    
    @property
    def ax(self):
        """Get the slider axes."""
        return self._slider.ax
