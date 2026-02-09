"""
Reference Charts PDF Generator

Creates a 5-page PDF with standard reference charts for V2 snapshots.
Pages 1-4 contain 3 charts each, Page 5 contains 1 chart (same size as others).
"""

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from tkinter import filedialog
from ui.chart_renderer import ChartRenderer
from domain.chart_config import ChartConfig, AxisConfig
from domain.snaptypes import SnapType
from version import APP_VERSION
import os


def V2_show_all_reference_charts(main_app, snaptype: SnapType):
    """
    Creates a 5-page PDF file with reference charts.
    Pages 1-4 have 3 charts each, Page 5 has 1 chart (same size as others).
    Each page has a different title.
    """
    
    # Define all chart configurations (13 charts total)
    # Each page definition: (page_title, list of chart configs)
    pages = [
        # Page 1: Operating Conditions
        {
            "title": "Operating Conditions",
            "charts": [
                {
                    "title": "Engine Speed",
                    "primary_pids": ["Epm_nEng"]
                },
                {
                    "title": "TPS",
                    "primary_pids": ["APP_r"],
                },
                {
                    "title": "Torque",
                    "primary_pids": ["PthSet_TrqInrSet"],
                }
            ]
        },
        
        #Page 2: Temperatures
        {
            "title": "Temperatures",
            "charts": [
                {
                    "title": "Fuel and Coolant",
                    "primary_pids": ["FuelT_t", "CEngDsT_t"],
                    "primary_min": -20,
                    "primary_max": 250,
                },
                {
                    "title": "Air Temperature",
                    "primary_pids": ["Air_tAFS"],
                    "primary_min": -20,
                    "primary_max": 110,
                },
                {
                    "title": "Oil Temperature",
                    "primary_pids": ["Oil_tSwmp"],
                    "primary_min": -20,
                    "primary_max": 250,
                }
            ]
        },
        
        # Page 3: Fuel System
        {
            "title": "Fuel System",
            "charts": [
                {
                    "title": "Rail Pressure",
                    "primary_pids": ["RailP_pFlt","Rail_pSetPoint"],
                },
                {
                    "title": "IMV Current",
                    "primary_pids": ["MeUn_iActFlt","MeUn_iSet"],
                },
                {
                    "title": "Fuel Quantity",
                    # The pre-injection PID names get corrected if they have an underscore in front of the [0]
                    "primary_pids": ["InjCrv_qMI1Des","InjCrv_qPiI1Des[0]","InjCrv_qPiI2Des[0]","InjCrv_qPiI3Des[0]"],
                }
            ]
        },
        
        # Page 4: Air Circuit
        {
            "title": "Air Circuit",
            "charts": [
                {
                    "title": "MAF",
                    "primary_pids": ["AFS_dm", "AirMod_mfGasIntkVlv_f"],
                },
                {
                    "title": "MAP",
                    "primary_pids": ["Air_pIntkVUs", "EnvP_p"],
                },
                {
                    "title": "EGR Position",
                    "primary_pids": ["EGRVlv_rAct", "EGRVlv_r"],
                    "primary_min": -10,
                    "primary_max": 110,
                }
            ]
        },
        
        # Page 5: Oil Pressure (single chart)
        {
            "title": "Oil Pressure",
            "charts": [
                {
                    "title": "Oil Pressure",
                    "primary_pids": ["Oil_pSwmp"],
                }
            ]
        }
    ]
    
    # Prompt user for save location
    pdf_filename = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile="V2_Reference_Charts.pdf",
        title="Save Reference Charts PDF"
    )
    
    if not pdf_filename:
        return  # User cancelled
    
    with PdfPages(pdf_filename) as pdf:
        for page_num, page in enumerate(pages, start=1):
            page_title = page["title"]
            charts = page["charts"]
            num_charts = len(charts)
            
            # Create figure for this page (landscape letter size)
            fig = Figure(figsize=(11, 8.5), dpi=150)
            
            # Add page title at the top
            fig.suptitle(page_title, fontsize=16, fontweight='bold', y=0.96)
            
            # Create all subplots at once for consistent vertical layout
            # Always create 3 rows to keep chart sizes consistent
            axes_col = fig.subplots(3, 1)
            
            # For pages with fewer than 3 charts, hide unused axes
            if num_charts == 1:
                axes_col[0].set_visible(False)
                axes_col[2].set_visible(False)
                axes_to_use = [axes_col[1]]  # Use middle position
            else:
                axes_to_use = list(axes_col)
            
            for chart_idx, chart_config in enumerate(charts):
                ax_left = axes_to_use[chart_idx]
                
                # Extract config values with defaults for optional fields
                primary_pids = chart_config.get("primary_pids", [])
                primary_min = chart_config.get("primary_min", None)
                primary_max = chart_config.get("primary_max", None)
                secondary_pids = chart_config.get("secondary_pids", [])
                secondary_min = chart_config.get("secondary_min", None)
                secondary_max = chart_config.get("secondary_max", None)
                
                # Create secondary axis if needed
                ax_right = None
                if secondary_pids:
                    ax_right = ax_left.twinx()
                
                # Build ChartConfig
                config = ChartConfig(
                    data=main_app.engine.snapshot,
                    chart_type="line",
                    primary_axis=AxisConfig(
                        series=primary_pids,
                        min_value=primary_min,
                        max_value=primary_max,
                        auto_scale=(primary_min is None or primary_max is None)
                    ),
                    secondary_axis=AxisConfig(
                        series=secondary_pids,
                        min_value=secondary_min,
                        max_value=secondary_max,
                        auto_scale=(secondary_min is None or secondary_max is None)
                    ),
                    title=chart_config["title"],
                    pid_info=main_app.engine.pid_info,
                    file_name=main_app.engine.file_name,
                    date_time=main_app.engine.date_time,
                    engine_hours=main_app.engine.hours
                )
                
                # Render the chart
                renderer = ChartRenderer(config)
                renderer._render_line_chart(ax_left, ax_right, config.data)
                renderer._apply_formatting(ax_left, ax_right)
                
                # Move chart title to left side (y-axis label position) for more vertical space
                # Get units from pid_info for the first primary PID
                chart_title = chart_config["title"]
                if primary_pids and main_app.engine.pid_info:
                    first_pid = primary_pids[0]
                    pid_info = main_app.engine.pid_info.get(first_pid, {})
                    unit = pid_info.get("Unit", "")
                    if unit:
                        chart_title = f"{chart_title} ({unit})"
                
                ax_left.set_ylabel(chart_title, fontsize=8, fontweight='bold')
                ax_left.set_title("")  # Remove top title
                ax_left.set_xlabel("")  # Remove x-axis label for more vertical space
            
            # Add chain of custody metadata at the top
            metadata_parts = []
            if main_app.engine.file_name:
                metadata_parts.append(f"File: {main_app.engine.file_name}")
            if main_app.engine.date_time:
                metadata_parts.append(f"Date/Time: {main_app.engine.date_time}")
            if main_app.engine.hours is not None and main_app.engine.hours > 0:
                metadata_parts.append(f"Engine Hours: {main_app.engine.hours}")
            
            if metadata_parts:
                metadata_text = "  |  ".join(metadata_parts)
                fig.text(0.5, 0.99, metadata_text, 
                        ha='center', va='top', fontsize=8, color='gray', style='italic')
            
            # Add page number at the bottom
            fig.text(0.5, 0.02, f'Page {page_num} of {len(pages)}', 
                    ha='center', va='bottom', fontsize=8, color='gray')
            
            # Add watermark
            fig.text(0.99, 0.01, f'Snapshot Decoder {APP_VERSION}', 
                    ha='right', va='bottom', fontsize=8, color='lightgray', alpha=0.7)
            
            # Adjust layout to prevent overlapping
            fig.tight_layout(rect=[0.02, 0.04, 0.98, 0.92])
            
            # Save the figure to the PDF
            pdf.savefig(fig, dpi=150)
            
            # Clean up
            fig.clf()
            del fig
    
    print(f"Reference charts PDF saved to: {pdf_filename}")
