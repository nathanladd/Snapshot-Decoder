"""
Color Manager

Manages color coordination between chart and UI elements, ensuring
primary and secondary axes always use distinct colors.
"""

from typing import Dict, Optional
import matplotlib.colors as mcolors


class ColorManager:
    """Manages color coordination between chart and UI elements."""
    
    # Define distinct color palettes for primary and secondary axes
    PRIMARY_COLORS = [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange  
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Lime
        '#17becf',  # Cyan
    ]
    
    SECONDARY_COLORS = [
        '#17becf',  # Cyan
        '#bcbd22',  # Lime
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#c49c94',  # Light brown
        '#f7b6d2',  # Light pink
        '#c7c7c7',  # Light gray
        '#dbdb8d',  # Light lime
        '#9edae5',  # Light cyan
        '#f7b6d2',  # Light pink (duplicate for variety)
    ]
    
    @classmethod
    def get_series_color(cls, series_name: str, is_secondary: bool, series_index: int, 
                        custom_styles: Optional[Dict] = None) -> str:
        """
        Get color for a series, ensuring axis distinction.
        
        Args:
            series_name: Name of the series
            is_secondary: Whether this is a secondary axis series
            series_index: Index of the series in its axis
            custom_styles: Dictionary of custom series styles
            
        Returns:
            Hex color string
        """
        # Check for custom style first
        if custom_styles and series_name in custom_styles:
            custom_style = custom_styles[series_name]
            if hasattr(custom_style, 'color') and custom_style.color:
                return custom_style.color
        
        # Use appropriate palette
        colors = cls.SECONDARY_COLORS if is_secondary else cls.PRIMARY_COLORS
        return colors[series_index % len(colors)]
    
    @classmethod
    def get_listbox_background(cls, color: str, alpha: float = 0.3) -> str:
        """
        Create lighter background version for listbox.
        
        Args:
            color: Hex color string
            alpha: Transparency factor (0-1, higher = more white)
            
        Returns:
            Lightened hex color string
        """
        if color.startswith('#'):
            # Convert hex to RGB
            rgb = [int(color[i:i+2], 16) for i in (1, 3, 5)]
            
            # Lighten by blending with white
            light_rgb = [int(c + (255 - c) * alpha) for c in rgb]
            
            return f'#{light_rgb[0]:02x}{light_rgb[1]:02x}{light_rgb[2]:02x}'
        
        # For named colors, convert to RGB first
        try:
            rgba = mcolors.to_rgba(color)
            rgb = [int(c * 255) for c in rgba[:3]]
            light_rgb = [int(c + (255 - c) * alpha) for c in rgb]
            return f'#{light_rgb[0]:02x}{light_rgb[1]:02x}{light_rgb[2]:02x}'
        except ValueError:
            return color  # Return original if conversion fails
    
    @classmethod
    def get_contrast_text_color(cls, background_color: str) -> str:
        """
        Get contrasting text color (black or white) for given background.
        
        Args:
            background_color: Hex color string
            
        Returns:
            'black' or 'white' depending on contrast
        """
        if background_color.startswith('#'):
            # Convert hex to RGB
            rgb = [int(background_color[i:i+2], 16) for i in (1, 3, 5)]
            
            # Calculate luminance (perceived brightness)
            luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
            
            # Return black for light backgrounds, white for dark backgrounds
            return 'black' if luminance > 0.5 else 'white'
        
        return 'black'  # Default to black for unknown colors
