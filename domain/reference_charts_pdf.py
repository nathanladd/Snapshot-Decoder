"""
Reference Charts PDF Generator

Creates a 5-page PDF with standard reference charts for V2 snapshots.
Pages 1-4 contain 3 charts each, Page 5 contains 1 chart (same size as others).
"""

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
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
        # Page 1: Electrical System
        {
            "title": "Electrical System Reference",
            "charts": [
                {
                    "title": "Battery Test",
                    "primary_pids": ["BattU_u"],
                    "primary_min": 0,
                    "primary_max": 18,
                    "secondary_pids": ["Epm_nEng"],
                    "secondary_min": -50,
                    "secondary_max": 3000
                },
                {
                    "title": "IMV Current",
                    "primary_pids": ["IMV_I", "IMV_IDem"],
                    "primary_min": 0,
                    "primary_max": 1050,
                    "secondary_pids": [],
                    "secondary_min": None,
                    "secondary_max": None
                },
                {
                    "title": "Starter System",
                    "primary_pids": ["BattU_u"],
                    "primary_min": 0,
                    "primary_max": 20,
                    "secondary_pids": ["Epm_nEng"],
                    "secondary_min": -50,
                    "secondary_max": 500
                }
            ]
        },
        
        # Page 2: Fuel System
        {
            "title": "Fuel System Reference",
            "charts": [
                {
                    "title": "Rail Pressure",
                    "primary_pids": ["RailP_pFlt", "Rail_pSetPoint"],
                    "primary_min": -15,
                    "primary_max": 30000,
                    "secondary_pids": [],
                    "secondary_min": None,
                    "secondary_max": None
                },
                {
                    "title": "Rail Gap",
                    "primary_pids": ["Rail_pDvt"],
                    "primary_min": -50,
                    "primary_max": 4000,
                    "secondary_pids": [],
                    "secondary_min": None,
                    "secondary_max": None
                },
                {
                    "title": "Fuel Delivery",
                    "primary_pids": ["InjCrv_qPiI1Des"],
                    "primary_min": -5,
                    "primary_max": 100,
                    "secondary_pids": ["IMV_I"],
                    "secondary_min": 0,
                    "secondary_max": 1050
                }
            ]
        },
        
        # Page 3: Temperature System
        {
            "title": "Temperature System Reference",
            "charts": [
                {
                    "title": "Engine Coolant & Fuel Temp",
                    "primary_pids": ["CEngDsT_t", "FuelT_t"],
                    "primary_min": -40,
                    "primary_max": 290,
                    "secondary_pids": [],
                    "secondary_min": None,
                    "secondary_max": None
                },
                {
                    "title": "Exhaust Gas Temperature",
                    "primary_pids": ["ExhMnfT_t"],
                    "primary_min": 0,
                    "primary_max": 800,
                    "secondary_pids": [],
                    "secondary_min": None,
                    "secondary_max": None
                },
                {
                    "title": "Intake Air Temperature",
                    "primary_pids": ["AirT_t"],
                    "primary_min": -40,
                    "primary_max": 150,
                    "secondary_pids": ["Epm_nEng"],
                    "secondary_min": -50,
                    "secondary_max": 3000
                }
            ]
        },
        
        # Page 4: Air & Boost System
        {
            "title": "Air & Boost System Reference",
            "charts": [
                {
                    "title": "Manifold Pressures",
                    "primary_pids": ["Boost_p", "BoostPre_pSet"],
                    "primary_min": -20,
                    "primary_max": 150,
                    "secondary_pids": ["Epm_nEng"],
                    "secondary_min": -50,
                    "secondary_max": 6250
                },
                {
                    "title": "Turbo Speed",
                    "primary_pids": ["TrbCh_nTrb"],
                    "primary_min": 0,
                    "primary_max": 300000,
                    "secondary_pids": ["Epm_nEng"],
                    "secondary_min": -50,
                    "secondary_max": 6250
                },
                {
                    "title": "Intake Throttle",
                    "primary_pids": ["Thr_rAct", "Thr_rDes"],
                    "primary_min": 0,
                    "primary_max": 140,
                    "secondary_pids": [],
                    "secondary_min": None,
                    "secondary_max": None
                }
            ]
        },
        
        # Page 5: Engine Performance (single chart)
        {
            "title": "Engine Performance Reference",
            "charts": [
                {
                    "title": "Engine Speed & Torque",
                    "primary_pids": ["Epm_nEng"],
                    "primary_min": -50,
                    "primary_max": 6250,
                    "secondary_pids": ["CoETS_rTrq"],
                    "secondary_min": -100,
                    "secondary_max": 110
                }
            ]
        }
    ]
    
    # Create PDF filename
    pdf_filename = os.path.join(os.path.expanduser("~"), "Desktop", "V2_Reference_Charts.pdf")
    
    with PdfPages(pdf_filename) as pdf:
        for page_num, page in enumerate(pages, start=1):
            page_title = page["title"]
            charts = page["charts"]
            num_charts = len(charts)
            
            # Create figure for this page (landscape letter size)
            fig = Figure(figsize=(11, 8.5), dpi=150)
            
            # Add page title at the top
            fig.suptitle(page_title, fontsize=16, fontweight='bold', y=0.96)
            
            # Create subplots based on number of charts
            # For 3 charts: 1 row, 3 columns
            # For 1 chart: 1 row, 3 columns but only use the middle one (same size)
            for chart_idx, chart_config in enumerate(charts):
                if num_charts == 3:
                    # 3 charts in a row
                    ax_left = fig.add_subplot(1, 3, chart_idx + 1)
                else:
                    # 1 chart centered (use middle position of 3-column layout)
                    ax_left = fig.add_subplot(1, 3, 2)
                
                # Create secondary axis if needed
                ax_right = None
                if chart_config["secondary_pids"]:
                    ax_right = ax_left.twinx()
                
                # Build ChartConfig
                config = ChartConfig(
                    data=main_app.engine.snapshot,
                    chart_type="line",
                    primary_axis=AxisConfig(
                        series=chart_config["primary_pids"],
                        min_value=chart_config["primary_min"],
                        max_value=chart_config["primary_max"],
                        auto_scale=False
                    ),
                    secondary_axis=AxisConfig(
                        series=chart_config["secondary_pids"],
                        min_value=chart_config["secondary_min"],
                        max_value=chart_config["secondary_max"],
                        auto_scale=False if chart_config["secondary_min"] is not None else True
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
                
                # Set chart title
                ax_left.set_title(chart_config["title"], fontsize=10, fontweight='bold', pad=8)
            
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
