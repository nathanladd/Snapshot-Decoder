"""
V1 ECU quick chart definitions.

These are declarative definitions for charts available when
viewing V1 ECU snapshot data.
"""

from domain.quick_charts.definitions import QuickChartDef, StatusChartDef


V1_BATTERY_TEST = QuickChartDef(
    action_id="V1_BATTERY_TEST",
    title="Battery Voltage",
    primary_pids=["P_L_Battery_raw"],
    primary_range=(0, 18),
    secondary_pids=["IN_Engine_cycle_speed"],
    secondary_range=(-50, 6250),
)

V1_RAIL_PRESSURE = QuickChartDef(
    action_id="V1_RAIL_PRESSURE",
    title="Rail Pressure",
    primary_pids=["RPC_Rail_pressure_dmnd", "P_L_RAIL_PRES_RAW"],
    primary_range=(-15, 30000),
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
    primary_pids=["ACM_INTAKE_PORT_AIR_FLOW_SPD", "ACM_INTAKE_PORT_AIR_FLOW_MAF", "ACM_Air_estimation_raw_error"],
    primary_range=(0, 150),
    secondary_pids=["IN_Egr_position"],
    secondary_range=(-10, 400),
)

V1_EGR_CALIBRATION = QuickChartDef(
    action_id="V1_EGR_CALIBRATION",
    title="EGR Calibration",
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

V1_TORQUE_CONTROL = QuickChartDef(
    action_id="V1_TORQUE_CONTROL",
    title="Torque",
    primary_pids=["T_D_Actual_brake_torque", "T_D_Max_brake_torque"],
    # Auto-scale when no range specified
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
    "V1_IMV_CURRENT": V1_IMV_CURRENT,               # IMV Current
    "V1_TURBO": V1_TURBO,                           # Manifold Pressure vs Atmospheric Pressure
    "V1_EGR_FLOW": V1_EGR_FLOW,                     # Speed density vs MAF
    "V1_EGR_CALIBRATION": V1_EGR_CALIBRATION,       # EGR Calibration
    "V1_PISTON_DELTA": V1_PISTON_DELTA,             # Piston Delta Speed
    "V1_TORQUE_CONTROL": V1_TORQUE_CONTROL,         # Torque and Torque Limit
}
