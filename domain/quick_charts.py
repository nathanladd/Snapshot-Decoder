from typing import List
import pandas as pd
from domain.snaptypes import SnapType
from domain.constants import BUTTONS_BY_TYPE

# Quick Charts do not pass a chart config data class. I want this method to update all the 
# controlls on the main ui, then use 'plot chart' to update a chart config.
def apply_quick_chart_setup(
    main_app, snaptype: SnapType, action_id: str, primary_pids: List[str], primary_min: str = "", 
primary_max: str = "", secondary_pids: List[str]=[], secondary_min: str="", secondary_max: str="",
chart_type: str="line", primary_ticks: List[float]=None, primary_tick_labels: List[str]=None, 
show_legend: bool=True):

    # Retrieve tooltip for the chart title
    tooltip = None
    if snaptype in BUTTONS_BY_TYPE:
        for button_name, cmd, tip in BUTTONS_BY_TYPE[snaptype]:
            if cmd == action_id:
                tooltip = tip
                break
    
    # Set scripted PID names for primary and secondary axes
    main_app.primary_series = primary_pids
    main_app.secondary_series = secondary_pids
    
    # Update list boxes
    main_app.primary_list.delete(0, 'end')
    for pid in main_app.primary_series:
        main_app.primary_list.insert('end', pid)
    
    main_app.secondary_list.delete(0, 'end')
    for pid in main_app.secondary_series:
        main_app.secondary_list.insert('end', pid)
    
    # Set scripted min/max values for axes
    if primary_min and primary_max:
        main_app.primary_auto.set(False)
        main_app.primary_ymin.set(primary_min)
        main_app.primary_ymax.set(primary_max)
    else:
        main_app.primary_auto.set(True)
    
    if secondary_min and secondary_max:
        main_app.secondary_auto.set(False)
        main_app.secondary_ymin.set(secondary_min)
        main_app.secondary_ymax.set(secondary_max)
    else:
        main_app.secondary_auto.set(True)
    
    # Trigger toggle to update entry states
    main_app._toggle_primary_inputs()
    main_app._toggle_secondary_inputs()
    
    # Set chart type
    if hasattr(main_app, 'chart_type_var'):
        main_app.chart_type_var.set(chart_type)

    # Set custom ticks
    if hasattr(main_app, 'primary_ticks'):
        main_app.primary_ticks = primary_ticks
        main_app.primary_tick_labels = primary_tick_labels

    # Set legend visibility
    if hasattr(main_app, 'show_legend_var'):
        main_app.show_legend_var.set(show_legend)

    # Generate the chart
    main_app.plot_combo_chart()
    
    # Set custom title if tooltip found
    if tooltip:
        main_app.ax_left.set_title(tooltip)
        # Update working_config title to match so toolbar has correct title for PDF export
        if main_app.working_config:
            main_app.working_config.title = tooltip
        main_app.canvas.draw_idle()

# ----------------------------------------------------------------------------
# ----------------------------------V1 Charts----------------------------------
# ----------------------------------------------------------------------------

def V1_show_battery_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_BATTERY_TEST",
        ["P_L_Battery_raw"],
        "0",
        "18",
        ["IN_Engine_cycle_speed"],
        "-50",
        "6250"
    )
    
def V1_show_rail_pressure_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_RAIL_PRESSURE",
        ["RPC_Rail_pressure_dmnd", "P_L_RAIL_PRES_RAW"],
        "-15",
        "30000",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )

def V1_show_rail_gap_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_RAIL_GAP",
        ["RPC_Rail_pressure_error"],
        "-5000",
        "5000",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )
    
def V1_show_imv_current_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_IMV_CURRENT",
        ["RPC_Im_crt_dmnd", "P_L_Im_crt_fb"],
        "0",
        "1050",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )

def V1_show_turbo_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_TURBO",
        ["P_L_MAP_RAW", "P_L_Atmosp_raw"],
        "-10",
        "35",
        ["IN_Engine_cycle_speed"],
        "-50",
        "6250"
    )

def V1_show_EGR_flow_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_EGR_FLOW",
        ["ACM_INTAKE_PORT_AIR_FLOW_SPD", "ACM_INTAKE_PORT_AIR_FLOW_MAF"],
        "0",
        "150",
        ["IN_Egr_position"],
        "-10",
        "400"
    )

def V1_show_EGR_position_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_EGR_POSITION",
        ["P_L_Egr_close_pos_mean_nvv", "P_L_Egr_feedback_pos_cnts"],
        "0",
        "1000",
        ["ACM_Egr_position_dmnd"],
        "-10",
        "400"
    )

def V1_show_piston_delta_chart(main_app, snaptype: SnapType):
    # Filter PIDs to only include those present in the snapshot (for 3 cylinder engine 1.8L)
    all_cylinders = ["IN_Bal_delta_speed[0]", "IN_Bal_delta_speed[1]", "IN_Bal_delta_speed[2]", "IN_Bal_delta_speed[3]"]
    cylinders_present = [pid for pid in all_cylinders if pid in main_app.engine.snapshot.columns]
    
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_PISTON_DELTA",
        cylinders_present,
        "-100",
        "100",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )

def V1_show_cam_crank_chart(main_app, snaptype: SnapType):
    pids = ["P_L_aps_sync_tasks_enabled", "P_L_aps_crank_valid", "P_L_aps_cam_valid"]
    
    # Y-axis limits and tick positions are auto-calculated by the chart renderer
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_CAM_CRANK",
        pids,
        chart_type="status",
        show_legend=True
    )

def V1_show_start_aid_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_START_AID",
        ["SAC_Glow_plug_output"],
        "-10",
        "4",
        ["SMC_ENGINE_STATE"],
        "-2",
        "10"
    )

def V1_show_air_fuel_ratio_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_AIR_FUEL_RATIO",
        ["AFC_Air_fuel_ratio"],
        "-50",
        "130",
        ["T_D_Smoke_limit_active"],
        "-2",
        "10"
    )

def V1_show_torque_control_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_TORQUE_CONTROL",
        ["T_D_Actual_brake_torque", "T_D_Max_brake_torque"]
        
    )

# ----------------------------------------------------------------------------
# ----------------------------------V2 Charts----------------------------------
# ----------------------------------------------------------------------------

def V2_show_battery_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_BATTERY_TEST",
        ["BattU_u"],
        "0",
        "18",
        ["Epm_nEng"],
        "-50",
        "3000"
    )

def V2_show_rail_pressure_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_RAIL_PRESSURE",
        ["RailP_pFlt", "Rail_pSetPoint"],
        "-15", "30000"  
    )

def V2_show_rail_gap_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_RAIL_GAP",
        ["Rail_pDvt"],
        "-50","4000"
    )

def V2_show_imv_current_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_IMV_CURRENT",
        ["MeUn_iActFlt", "MeUn_iSet"],
    )

def V2_show_turbo_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_TURBO",
        ["Air_pIntkVUs", "EnvP_p"],
        "-20",
        "35",
        ["InjCrv_qMI1Des"],
        "-5",
        "200"
    )

def V2_show_misfire_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_MISFIRE",
        ["MisfDet_ctMifMem_[0]", "MisfDet_ctMifMem_[2]", "MisfDet_ctMifMem_[3]","MisfDet_ctMifMem_[1]"],
        "-20","150"
    )

def V2_show_throttle_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_THROTTLE_VALVE",
        ["ThrVlv_r", "ThrVlv_rAct"],
        "-5",
        "140"
    )

def V2_show_load_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_ENGINE_LOAD",
        ["CoETS_rTrq"],
        "-100","110",
        ["PthSet_TrqInrSet"],
        "0","800"
    )

def V2_show_engine_torque_limits(main_app, snaptype: SnapType):
    col_name = "CoETS_stCurrLimActive"
    
    # Check if data exists
    if not main_app.engine or col_name not in main_app.engine.snapshot.columns:
        return

    # Parse the string of digits into individual columns
    # Assuming the column contains strings like "00101"
    s = main_app.engine.snapshot[col_name].astype(str)
    
    # Create a temporary DataFrame where each character is a column
    # map(list) converts "010" to ['0', '1', '0']
    split_df = pd.DataFrame(s.map(list).tolist(), index=main_app.engine.snapshot.index)
    
    # Convert to numeric (0s and 1s)
    split_df = split_df.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    
    # Define column names
    # this list must exactly match the number of digits in the column 
    column_names = ["System Error Event", "Differential Protection", "Engine Mechanics Protection", "Smoke Limit", "Not Used", 
    "Overheating", "Limit Travel", " Maximum Gearbox Input Torque", "Injection Quantity Limitation", "High Pressure Pump",
    "Speed Limitation", "Protection From Exessive Torque", "Slow Path Limitation", "Inner Engine Torque", "Engine Protection"]
    
    # Assign names to the split dataframe
    # Handle case where actual digits might be fewer/more than expected names
    # We take the minimum length
    num_cols = min(len(column_names), split_df.shape[1])
    split_df = split_df.iloc[:, :num_cols]
    final_names = column_names[:num_cols]
    # Do NOT rename split_df columns to avoid issues with duplicate names
    
    # Add new columns to the main snapshot DataFrame
    new_cols_added = []
    
    for i, col_name in enumerate(final_names):
        # Always update the column if it exists to ensure offset is applied correctly for this chart view
        # We create a new column specific for plotting to avoid modifying original data permanently if we want to keep raw 0/1 elsewhere
        # But since these are generated columns, it's fine to overwrite or create new display columns
        
        # Use a display-specific column name to avoid confusion with raw values
        # Include category name to ensure uniqueness even if col_name is duplicated
        display_col = f"Torque Limit:_{col_name}"
        
        # Get 0/1 values by position
        vals = split_df.iloc[:, i]
        
        # For status chart, we don't offset the data. The renderer handles stacking.
        # We just pass the raw 0/1 values.
        main_app.engine.snapshot[display_col] = vals
        new_cols_added.append(display_col)
    
    # Update the UI PID list so the new columns appear
    if new_cols_added and hasattr(main_app, 'pid_list'):
        for col in new_cols_added:
            if col not in main_app.pid_list.get(0, 'end'):
                main_app.pid_list.insert('end', col)

    # Y-axis limits and tick positions are auto-calculated by the chart renderer
    # based on the number of series (1.5 spacing per series)
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_ENGINE_TORQUE_LIMITS",
        new_cols_added,
        chart_type="status",
        show_legend=False
    )

# ----------------------------------------------------------------------------
# ---------------------------------- EUD_V1 ----------------------------------
# ----------------------------------------------------------------------------

def V1EUD_show_speed_load_chart(main_app, snaptype: SnapType):
    """Build a speed vs load bubble chart from EUD timer data."""
    
    # Get total engine run time in seconds (convert to float in case it's stored as string)
    engine_run_time = float(main_app.engine.snapshot['EUD_Engine_run_time_total_nvv'].iloc[0])
    
    # Speed mapping: index -> RPM (0=900, 1=1100, 2=1300, etc.)
    speed_map = {i: 900 + (i * 200) for i in range(16)}  # Adjust range as needed
    
    # Load mapping: index -> percent (0=5%, 1=15%, 2=25%, etc.)
    load_map = {i: 5 + (i * 10) for i in range(11)}  # Adjust range as needed
    
    # Build the DataFrame by looping through all EUD_Spdload_blm_timer_nvv[*,*] columns
    rows = []
    snapshot = main_app.engine.snapshot
    
    for col in snapshot.columns:
        if col.startswith('EUD_Spdload_blm_timer_nvv['):
            # Parse indices from column name like "EUD_Spdload_blm_timer_nvv[0,0]"
            try:
                indices = col.split('[')[1].rstrip(']').split(',')
                speed_idx = int(indices[0])
                load_idx = int(indices[1])
                
                # Get the timer value (seconds at this speed/load)
                timer_value = float(snapshot[col].iloc[0])
                
                # Calculate percent of total run time
                if engine_run_time > 0:
                    percent = (timer_value / engine_run_time) * 100
                else:
                    percent = 0
                
                # Map indices to actual speed and load values
                speed = speed_map.get(speed_idx, speed_idx)
                load = load_map.get(load_idx, load_idx)
                
                rows.append({
                    'Speed': speed,
                    'Load': load,
                    'Percent': percent
                })
            except (IndexError, ValueError):
                continue
    
    # Create DataFrame
    speed_load_df = pd.DataFrame(rows)
    
    # Filter out zero-percent entries for cleaner visualization
    speed_load_df = speed_load_df[speed_load_df['Percent'] > 0]
    
    # Clear and set up the chart axes
    main_app.figure.clear()
    ax = main_app.figure.add_subplot(111)
    
    # Create scatter plot with size based on Percent
    # Scale the sizes based on figure area (reference: thumbnail at 4x2 = 8 sq inches)
    fig_width, fig_height = main_app.figure.get_size_inches()
    fig_area = fig_width * fig_height
    thumbnail_area = 4 * 2  # 8 sq inches
    area_ratio = fig_area / thumbnail_area
    base_scale = 50.0 * area_ratio
    sizes = speed_load_df['Percent'] * base_scale
    
    scatter = ax.scatter(
        speed_load_df['Speed'],
        speed_load_df['Load'],
        s=sizes,
        alpha=0.6,
        c=speed_load_df['Percent'],  # Color by percent too
        cmap='viridis',
        edgecolors='black',
        linewidth=0.5
    )
    
    # Add colorbar to show percent scale
    cbar = main_app.figure.colorbar(scatter, ax=ax)
    cbar.set_label('% of Run Time')
    
    # Labels and title
    ax.set_xlabel('Engine Speed (RPM)')
    ax.set_ylabel('Load (%)')
    ax.set_title('Speed vs Load Distribution')
    ax.grid(True, alpha=0.3)
    
    # Store axes reference
    main_app.ax_left = ax
    main_app.ax_right = None
    
    # Update canvas
    main_app.canvas.draw()
    
    # Update working_config for consistency (with custom data)
    from domain.chart_config import ChartConfig, AxisConfig
    main_app.working_config = ChartConfig(
        data=speed_load_df,
        chart_type="bubble",
        primary_axis=AxisConfig(series=['Load'], auto_scale=True),
        secondary_axis=AxisConfig(series=[], auto_scale=True),
        title="Speed vs Load Distribution",
        x_column="Speed",
        bubble_size_column="Percent",
        bubble_size_scale=50.0
    )
    
def V1EUD_show_speed_band_chart(main_app, snaptype: SnapType):
    """
    Build a bar chart showing speed band run times from Frame 0 values.
    Converts seconds to hours for display.
    """
    from domain.chart_config import ChartConfig, AxisConfig
    from ui.chart_renderer import ChartRenderer
    
    # Column names for speed bands
    columns = [
        "EUD_Engine_run_time_spdbnd1_nvv",
        "EUD_Engine_run_time_spdbnd2_nvv",
        "EUD_Engine_run_time_spdbnd3_nvv",
        "EUD_Engine_run_time_spdbnd4_nvv",
        "EUD_Engine_run_time_spdbnd5_nvv"
    ]
    
    # Display labels for the bars
    labels = ["< 1250", "1250-1600", "1600-2000", "2000-2400", "> 2400"]
    
    df = main_app.engine.snapshot
    
    # Get Frame 0 row
    frame_zero = df[df["Frame"] == 0]
    if frame_zero.empty:
        return
    
    # Extract values at Frame 0 and convert seconds to hours
    values = []
    for col in columns:
        if col in frame_zero.columns:
            try:
                seconds = float(frame_zero[col].iloc[0])
                hours = round(seconds / 3600, 2)
                values.append(hours)
            except (ValueError, IndexError, TypeError):
                values.append(0.0)
        else:
            values.append(0.0)
    
    # Create DataFrame for bar chart
    chart_data = pd.DataFrame({
        "Speed Band": labels,
        "Hours": values
    })
    
    # Create chart config
    config = ChartConfig(
        data=chart_data,
        chart_type="bar",
        primary_axis=AxisConfig(series=["Hours"], auto_scale=True),
        secondary_axis=AxisConfig(series=[], auto_scale=True),
        title="Speed Band Run Time",
        x_column="Speed Band",
        x_label="Speed Band",
        pid_info=main_app.engine.pid_info,
        file_name=main_app.engine.file_name,
        date_time=main_app.engine.date_time,
        engine_hours=main_app.engine.hours
    )
    
    # Render the chart
    main_app.working_config = config
    renderer = ChartRenderer(config)
    main_app.ax_left, main_app.ax_right = renderer.render(main_app.figure, main_app.canvas)
    main_app.toolbar.chart_config = config

def V1EUD_show_elevation_chart(main_app, snaptype: SnapType):
    """
    Build a bar chart showing atmospheric pressure PIDs converted to elevation.
    """
    from domain.chart_config import ChartConfig, AxisConfig
    from ui.chart_renderer import ChartRenderer
    
    # Column names for speed bands
    columns = [
        "EUD_Atmos_pres_timer_nvv[7]",
        "EUD_Atmos_pres_timer_nvv[6]",
        "EUD_Atmos_pres_timer_nvv[5]",
        "EUD_Atmos_pres_timer_nvv[4]",
        "EUD_Atmos_pres_timer_nvv[3]",
        "EUD_Atmos_pres_timer_nvv[2]",
        "EUD_Atmos_pres_timer_nvv[1]",
        "EUD_Atmos_pres_timer_nvv[0]"
    ]
    
    # Display labels for the bars
    labels = ["< Sea Level", "0-1,640 Ft", "1,640-3,280 Ft", "3,280-4,920 Ft", "4,920-6,560 Ft", "6,560-9,850 Ft", "9,850-13,120 Ft", ">13,120 Ft"]
    
    df = main_app.engine.snapshot
    
    # Get Frame 0 row
    frame_zero = df[df["Frame"] == 0]
    if frame_zero.empty:
        return
    
    # Extract values at Frame 0 and convert seconds to hours
    values = []
    for col in columns:
        if col in frame_zero.columns:
            try:
                seconds = float(frame_zero[col].iloc[0])
                hours = round(seconds / 3600, 2)
                values.append(hours)
            except (ValueError, IndexError, TypeError):
                values.append(0.0)
        else:
            values.append(0.0)
    
    # Create DataFrame for bar chart
    chart_data = pd.DataFrame({
        "Elevation": labels,
        "Hours": values
    })
    
    # Create chart config
    config = ChartConfig(
        data=chart_data,
        chart_type="bar",
        primary_axis=AxisConfig(series=["Hours"], auto_scale=True),
        secondary_axis=AxisConfig(series=[], auto_scale=True),
        title="Time at Elevation",
        x_column="Elevation",
        x_label="Elevation",
        pid_info=main_app.engine.pid_info,
        file_name=main_app.engine.file_name,
        date_time=main_app.engine.date_time,
        engine_hours=main_app.engine.hours
    )
    
    # Render the chart
    main_app.working_config = config
    renderer = ChartRenderer(config)
    main_app.ax_left, main_app.ax_right = renderer.render(main_app.figure, main_app.canvas)
    main_app.toolbar.chart_config = config

def V1EUD_show_EGT_chart(main_app, snaptype: SnapType):
    """
    Build a bar chart showing EGT hours.
    """
    from domain.chart_config import ChartConfig, AxisConfig
    from ui.chart_renderer import ChartRenderer
    
    # Column names for speed bands
    columns = [
        "EUD_Turbine_in_temp_timer_nvv[0]",
        "EUD_Turbine_in_temp_timer_nvv[1]",
        "EUD_Turbine_in_temp_timer_nvv[2]",
        "EUD_Turbine_in_temp_timer_nvv[3]",
        "EUD_Turbine_in_temp_timer_nvv[4]",
        "EUD_Turbine_in_temp_timer_nvv[5]",
        "EUD_Turbine_in_temp_timer_nvv[6]",
        "EUD_Turbine_in_temp_timer_nvv[7]"
    ]
    
    # Display labels for the bars
    labels = ["< 32F", "0-212F", "212-392F", "392-752F", "752-1112F", "1112-1292F", "1292-1382F", "1382-1562F"]
    
    df = main_app.engine.snapshot
    
    # Get Frame 0 row
    frame_zero = df[df["Frame"] == 0]
    if frame_zero.empty:
        return
    
    # Extract values at Frame 0
    values = []
    for col in columns:
        if col in frame_zero.columns:
            try:
                seconds = float(frame_zero[col].iloc[0])
                hours = round(seconds / 3600, 2)
                values.append(hours)
            except (ValueError, IndexError, TypeError):
                values.append(0.0)
        else:
            values.append(0.0)
    
    # Create DataFrame for bar chart
    chart_data = pd.DataFrame({
        "EGT": labels,
        "Hours": values
    })
    
    # Create chart config
    config = ChartConfig(
        data=chart_data,
        chart_type="bar",
        primary_axis=AxisConfig(series=["Hours"], auto_scale=True),
        secondary_axis=AxisConfig(series=[], auto_scale=True),
        title="Time at EGT",
        x_column="EGT",
        x_label="EGT",
        pid_info=main_app.engine.pid_info,
        file_name=main_app.engine.file_name,
        date_time=main_app.engine.date_time,
        engine_hours=main_app.engine.hours
    )
    
    # Render the chart
    main_app.working_config = config
    renderer = ChartRenderer(config)
    main_app.ax_left, main_app.ax_right = renderer.render(main_app.figure, main_app.canvas)
    main_app.toolbar.chart_config = config