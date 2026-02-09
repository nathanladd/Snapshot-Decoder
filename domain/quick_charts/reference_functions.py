"""
Reference chart functions for V2 architecture.

These functions integrate reference charts with the existing quick chart system.
"""

from PySide6.QtWidgets import QMessageBox
from ui.logger import error


def show_reference_chart(main_app, snaptype, action_id: str):
    """Show a reference chart using V2 architecture."""
    from .reference_builder import ReferenceChartBuilder
    
    # Create reference builder
    builder = ReferenceChartBuilder(main_app.engine, main_app)
    
    # Build the reference chart
    config = builder.build_reference_chart(action_id)
    if config:
        # Set as working config and render
        main_app.working_config = config
        from ui.chart_renderer import ChartRenderer
        renderer = ChartRenderer(config)
        main_app.ax_left, main_app.ax_right = renderer.render(main_app.figure, main_app.canvas)
        main_app.toolbar.chart_config = config
        
        # Update title to indicate reference chart
        main_app.ax_left.set_title(f"Reference: {config.title}")
        main_app.canvas.draw_idle()
    else:
        error(f"Reference chart '{action_id}' not found")


def generate_reference_pdf(main_app, snaptype):
    """Generate complete reference PDF using V2 architecture."""
    from .reference_builder import ReferenceChartBuilder
    
    # Create reference builder
    builder = ReferenceChartBuilder(main_app.engine, main_app)
    
    # Generate PDF
    file_path = builder.create_reference_pdf(snaptype)
    if file_path:
        # Show success message
        QMessageBox.information(
            main_app,
            "Reference PDF Generated",
            f"Reference charts PDF saved to:\n{file_path}"
        )
    else:
        # User cancelled or error occurred
        pass


# Individual reference chart functions
def REF_show_engine_speed(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_ENGINE_SPEED")

def REF_show_tps(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_TPS")

def REF_show_torque(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_TORQUE")

def REF_show_fuel_coolant_temp(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_FUEL_COOLANT_TEMP")

def REF_show_air_temp(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_AIR_TEMP")

def REF_show_oil_temp(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_OIL_TEMP")

def REF_show_rail_pressure(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_RAIL_PRESSURE")

def REF_show_imv_current(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_IMV_CURRENT")

def REF_show_fuel_quantity(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_FUEL_QUANTITY")

def REF_show_maf(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_MAF")

def REF_show_map(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_MAP")

def REF_show_egr_position(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_EGR_POSITION")

def REF_show_oil_pressure(main_app, snaptype):
    show_reference_chart(main_app, snaptype, "REF_OIL_PRESSURE")

def REF_generate_pdf(main_app, snaptype):
    generate_reference_pdf(main_app, snaptype)
