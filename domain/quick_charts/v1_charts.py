"""
V1 ECU quick chart definitions.

These are declarative definitions for charts available when
viewing V1 ECU snapshot data.
"""

from domain.quick_charts.definitions import QuickChartDef, StatusChartDef


V1_BATTERY_TEST = QuickChartDef(
    action_id="V1_BATTERY_TEST",
    title="Battery Voltage vs RPM",
    primary_pids=["P_L_Battery_raw"],
    primary_range=(0, 18),
    secondary_pids=["IN_Engine_cycle_speed"],
    secondary_range=(-50, 6250),
)

V1_RAIL_PRESSURE = QuickChartDef(
    action_id="V1_RAIL_PRESSURE",
    title="Rail Pressure vs Fuel Demand",
    primary_pids=["RPC_Rail_pressure_dmnd", "P_L_RAIL_PRES_RAW"],
    primary_range=(-15, 30000),
    secondary_pids=["FQD_Chkd_inj_fuel_dmnd"],
    secondary_range=(-5, 300),
)

V1_RAIL_GAP = QuickChartDef(
    action_id="V1_RAIL_GAP",
    title="Rail Pressure Error",
    primary_pids=["RPC_Rail_pressure_error"],
    primary_range=(-5000, 5000),
    secondary_pids=["FQD_Chkd_inj_fuel_dmnd"],
    secondary_range=(-5, 300),
)

V1_IMV_CURRENT = QuickChartDef(
    action_id="V1_IMV_CURRENT",
    title="IMV Current",
    primary_pids=["RPC_Im_crt_dmnd", "P_L_Im_crt_fb"],
    primary_range=(0, 1050),
    secondary_pids=["FQD_Chkd_inj_fuel_dmnd"],
    secondary_range=(-5, 300),
)

V1_TURBO = QuickChartDef(
    action_id="V1_TURBO",
    title="Boost Pressure",
    primary_pids=["P_L_MAP_RAW", "P_L_Atmosp_raw"],
    primary_range=(-10, 35),
    secondary_pids=["IN_Engine_cycle_speed"],
    secondary_range=(-50, 6250),
)

V1_EGR_FLOW = QuickChartDef(
    action_id="V1_EGR_FLOW",
    title="EGR Flow",
    primary_pids=["ACM_INTAKE_PORT_AIR_FLOW_SPD", "ACM_INTAKE_PORT_AIR_FLOW_MAF"],
    primary_range=(0, 150),
    secondary_pids=["IN_Egr_position"],
    secondary_range=(-10, 400),
)

V1_EGR_POSITION = QuickChartDef(
    action_id="V1_EGR_POSITION",
    title="EGR Position",
    primary_pids=["P_L_Egr_close_pos_mean_nvv", "P_L_Egr_feedback_pos_cnts"],
    primary_range=(0, 1000),
    secondary_pids=["ACM_Egr_position_dmnd"],
    secondary_range=(-10, 400),
)

V1_PISTON_DELTA = QuickChartDef(
    action_id="V1_PISTON_DELTA",
    title="Piston Delta Speed",
    primary_pids=["IN_Bal_delta_speed[0]", "IN_Bal_delta_speed[1]", 
                  "IN_Bal_delta_speed[2]", "IN_Bal_delta_speed[3]"],
    primary_range=(-100, 100),
    secondary_pids=["FQD_Chkd_inj_fuel_dmnd"],
    secondary_range=(-5, 300),
    # Dynamic filtering: only include PIDs that exist in the snapshot
    dynamic_primary_pids=["IN_Bal_delta_speed[0]", "IN_Bal_delta_speed[1]",
                          "IN_Bal_delta_speed[2]", "IN_Bal_delta_speed[3]"],
)

V1_CAM_CRANK = StatusChartDef(
    action_id="V1_CAM_CRANK",
    title="Cam/Crank Status",
    primary_pids=["P_L_aps_sync_tasks_enabled", "P_L_aps_crank_valid", "P_L_aps_cam_valid"],
    chart_type="status",
    show_legend=True,
)

V1_START_AID = QuickChartDef(
    action_id="V1_START_AID",
    title="Start Aid / Glow Plug",
    primary_pids=["SAC_Glow_plug_output"],
    primary_range=(-10, 4),
    secondary_pids=["SMC_ENGINE_STATE"],
    secondary_range=(-2, 10),
)

V1_AIR_FUEL_RATIO = QuickChartDef(
    action_id="V1_AIR_FUEL_RATIO",
    title="Air Fuel Ratio",
    primary_pids=["AFC_Air_fuel_ratio"],
    primary_range=(-50, 130),
    secondary_pids=["T_D_Smoke_limit_active"],
    secondary_range=(-2, 10),
)

V1_TORQUE_CONTROL = QuickChartDef(
    action_id="V1_TORQUE_CONTROL",
    title="Torque Control",
    primary_pids=["T_D_Actual_brake_torque", "T_D_Max_brake_torque"],
    # Auto-scale when no range specified
)

V1_FUEL_COOLANT_TEMP = QuickChartDef(
    action_id="V1_FUEL_COOLANT_TEMP",
    title="Fuel & Coolant Temperature",
    primary_pids=["P_L_Fuel_temp_raw", "P_L_Coolant_temperature"],
    primary_range=(-40, 290),
)


# Registry of all V1 charts by action_id

# 🔄 How It Works:
# Snapshot Detection: System determines if loaded data is V1 format
# Registry Selection: Uses V1_CHARTS instead of EUD_CHARTS
# UI Population: Quick chart panel shows V1-specific options
# Chart Generation: Selected chart definition builds the appropriate plot
# 💡 Example Flow:
# User loads V1 snapshot data
# Quick chart panel shows "Rail Pressure", "Turbo", etc.
# User clicks "V1_TURBO" → looks up in V1_CHARTS
# Gets V1_TURBO definition with boost pressure PIDs
# Creates line chart showing turbo performance

V1_CHARTS: dict[str, QuickChartDef] = {
    "V1_BATTERY_TEST": V1_BATTERY_TEST,             # Battery Test
    "V1_RAIL_PRESSURE": V1_RAIL_PRESSURE,           # Rail Pressure
    "V1_RAIL_GAP": V1_RAIL_GAP,                     # Rail Gap
    "V1_IMV_CURRENT": V1_IMV_CURRENT,               # IMV Current
    "V1_TURBO": V1_TURBO,                           # Manifold Pressure vs Atmospheric Pressure
    "V1_EGR_FLOW": V1_EGR_FLOW,                     # Speed density vs MAF
    "V1_EGR_POSITION": V1_EGR_POSITION,             # EGR Position
    "V1_PISTON_DELTA": V1_PISTON_DELTA,             # Piston Delta Speed
    "V1_CAM_CRANK": V1_CAM_CRANK,                   # Cam/Crank Status
    "V1_START_AID": V1_START_AID,                   # Start Aid / Glow Plug
    "V1_AIR_FUEL_RATIO": V1_AIR_FUEL_RATIO,         # Air Fuel Ratio
    "V1_TORQUE_CONTROL": V1_TORQUE_CONTROL,         # Torque Control
    "V1_FUEL_COOLANT_TEMP": V1_FUEL_COOLANT_TEMP,   # Fuel & Coolant Temperature
}
