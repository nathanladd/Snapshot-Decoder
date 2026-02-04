"""
Chart Controller - Handles chart rendering by delegating to appropriate renderers.

Manages the relationship between chart configurations and their visual representations.
No UI dependencies - pure chart rendering logic.
"""

from typing import Dict, Type
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from domain.chart_config import ChartConfig
from ui.chart_renderer import ChartRenderer
from infrastructure import get_logger, log_chart_generated, info, error, debug


class ChartController:
    """
    Handles chart rendering by delegating to appropriate renderer.
    
    Responsibilities:
    - Map chart types to renderer classes
    - Render charts to matplotlib figures
    - Generate thumbnails for previews
    - Log chart generation events
    """
    
    def __init__(self):
        self.logger = get_logger()
        info("ChartController initialized")
    
    def render(self, config: ChartConfig, figure: Figure) -> Figure:
        """
        Render chart config to the given figure.
        
        Args:
            config: Chart configuration containing all rendering parameters
            figure: Matplotlib figure to render onto
            
        Returns:
            The rendered figure (same object passed in)
            
        Raises:
            ValueError: If chart type is not supported
            Exception: If rendering fails
        """
        try:
            debug(f"Rendering chart: {config.chart_type}")
            
            # Create renderer and render
            renderer = ChartRenderer(config)
            rendered_figure = renderer._render_config(config)
            
            # Log successful chart generation
            pids = []
            if hasattr(config, 'primary_pids') and config.primary_pids:
                pids.extend(config.primary_pids)
            if hasattr(config, 'secondary_pids') and config.secondary_pids:
                pids.extend(config.secondary_pids)
            
            snapshot_file = getattr(config.snapshot, 'file_path', 'unknown') if hasattr(config, 'snapshot') else 'unknown'
            log_chart_generated(config.chart_type, pids, snapshot_file)
            
            info(f"Chart rendered successfully: {config.chart_type}")
            return rendered_figure
            
        except Exception as e:
            error(f"Chart rendering failed: {str(e)}")
            raise
    
    def render_thumbnail(self, config: ChartConfig, size: tuple = (200, 150)) -> Figure:
        """
        Render a thumbnail preview of the chart.
        
        Args:
            config: Chart configuration
            size: Thumbnail size as (width, height) in pixels
            
        Returns:
            Small matplotlib figure with thumbnail rendering
        """
        try:
            debug(f"Rendering thumbnail: {config.chart_type}")
            
            # Create small figure for thumbnail
            dpi = 100
            fig_width = size[0] / dpi
            fig_height = size[1] / dpi
            
            thumbnail_figure = Figure(figsize=(fig_width, fig_height), dpi=dpi)
            
            # Render at smaller scale
            renderer = ChartRenderer(config)
            renderer._render_config(config)
            
            # Log thumbnail generation
            debug(f"Thumbnail rendered: {config.chart_type}")
            return thumbnail_figure
            
        except Exception as e:
            error(f"Thumbnail rendering failed: {str(e)}")
            # Return empty figure on error
            error_figure = Figure(figsize=(size[0]/100, size[1]/100))
            ax = error_figure.add_subplot(111)
            ax.text(0.5, 0.5, "Error\nrendering\nthumbnail", 
                   ha='center', va='center', fontsize=8, color='red')
            ax.axis('off')
            return error_figure
    
    def get_supported_chart_types(self) -> list:
        """
        Get list of supported chart types.
        
        Returns:
            List of chart type strings that can be rendered
        """
        # This could be made more dynamic by discovering renderer classes
        return ['line', 'bar', 'bubble', 'status', 'scatter', 'histogram']
    
    def validate_config(self, config: ChartConfig) -> bool:
        """
        Validate chart configuration before rendering.
        
        Args:
            config: Chart configuration to validate
            
        Returns:
            True if configuration is valid for rendering
        """
        try:
            # Check basic required fields
            if not hasattr(config, 'chart_type') or not config.chart_type:
                error("Chart config missing chart_type")
                return False
            
            if config.chart_type not in self.get_supported_chart_types():
                error(f"Unsupported chart type: {config.chart_type}")
                return False
            
            # Check data availability
            if not hasattr(config, 'snapshot') or not config.snapshot:
                error("Chart config missing snapshot data")
                return False
            
            # Chart-type specific validation
            if config.chart_type in ['line', 'scatter']:
                if not hasattr(config, 'primary_pids') or not config.primary_pids:
                    error(f"{config.chart_type} chart requires primary_pids")
                    return False
            
            elif config.chart_type == 'bar':
                if not hasattr(config, 'primary_pids') or not config.primary_pids:
                    error("Bar chart requires primary_pids")
                    return False
            
            elif config.chart_type == 'bubble':
                if not hasattr(config, 'primary_pids') or len(config.primary_pids) < 2:
                    error("Bubble chart requires at least 2 primary_pids")
                    return False
            
            debug(f"Chart config validation passed: {config.chart_type}")
            return True
            
        except Exception as e:
            error(f"Chart config validation failed: {str(e)}")
            return False
    
    def clear_figure(self, figure: Figure):
        """
        Clear all plots from a figure.
        
        Args:
            figure: Matplotlib figure to clear
        """
        try:
            figure.clear()
            plt.close(figure)
            debug("Figure cleared")
        except Exception as e:
            error(f"Failed to clear figure: {str(e)}")
    
    def shutdown(self):
        """Clean shutdown of chart controller."""
        info("ChartController shutdown complete")
