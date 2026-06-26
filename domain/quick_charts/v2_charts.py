"""
V2 ECU quick chart definitions.

These are declarative definitions for charts available when
viewing V2 ECU snapshot data.
"""

from domain.quick_charts.definitions import QuickChartDef, StatusChartDef


V2_BATTERY_TEST = QuickChartDef(
    action_id="V2_BATTERY_TEST",
    title="Battery Voltage",
    primary_pids=["BattU_u"],
    primary_range=(0, 18),
    secondary_pids=["Epm_nEng"],
    secondary_range=(-50, 3000),
)

V2_RAIL_PRESSURE = QuickChartDef(
    action_id="V2_RAIL_PRESSURE",
    title="Rail Pressure",
    primary_pids=["RailP_pFlt", "Rail_pSetPoint"],
    primary_range=(-15, 30000),
)

V2_RAIL_GAP = QuickChartDef(
    action_id="V2_RAIL_GAP",
    title="Rail Pressure Error",
    primary_pids=["Rail_pDvt"],
    primary_range=(-50, 4000),
)

V2_IMV_CURRENT = QuickChartDef(
    action_id="V2_IMV_CURRENT",
    title="IMV Current",
    primary_pids=["MeUn_iActFlt", "MeUn_iSet"],
    # Auto-scale when no range specified
)

V2_TURBO = QuickChartDef(
    action_id="V2_TURBO",
    title="Boost Pressure",
    primary_pids=["Air_pIntkVUs", "EnvP_p"],
    primary_range=(-20, 35),
    secondary_pids=["InjCrv_qMI1Des"],
    secondary_range=(-5, 200),
)

V2_MISFIRE = QuickChartDef(
    action_id="V2_MISFIRE",
    title="Misfire Counters",
    primary_pids=["MisfDet_ctMifMem_[0]", "MisfDet_ctMifMem_[2]", 
                  "MisfDet_ctMifMem_[3]", "MisfDet_ctMifMem_[1]"],
)

V2_THROTTLE_VALVE = QuickChartDef(
    action_id="V2_THROTTLE_VALVE",
    title="Throttle Valve Position",
    primary_pids=["ThrVlv_r", "ThrVlv_rAct"],
    primary_range=(-5, 140),
)

V2_ENGINE_LOAD = QuickChartDef(
    action_id="V2_ENGINE_LOAD",
    title="Engine Torque",
    primary_pids=["PthSet_TrqInrSet"],
    primary_range=(0, 300),
    secondary_pids=["Oil_tSwmp"],
    secondary_range=(0, 240),
)

V2_ENGINE_TORQUE_LIMITS = StatusChartDef(
    action_id="V2_ENGINE_TORQUE_LIMITS",
    title="Engine Torque Limits",
    primary_pids=[],  # PIDs are generated dynamically from source_column
    chart_type="status",
    show_legend=False,
    # The source column contains a string of digits representing bit flags
    source_column="CoETS_stCurrLimActive",
    digit_labels=[
        "System Error Event",
        "Differential Protection",
        "Engine Mechanics Protection",
        "Smoke Limit",
        "Not Used",
        "Overheating",
        "Limit Travel",
        "Maximum Gearbox Input Torque",
        "Injection Quantity Limitation",
        "High Pressure Pump",
        "Speed Limitation",
        "Protection From Excessive Torque",
        "Slow Path Limitation",
        "Inner Engine Torque",
        "Engine Protection",
    ],
    display_prefix="Torque Limit:",
)

V2_BOOST_LEAK = QuickChartDef(
    action_id="V2_BOOST_LEAK",
    title="Boost Leak",
    primary_pids=["AirMod_mfGasIntkVlv_f", "AFS_dm"],
    primary_range=(0, 400),
    secondary_pids=["EGRVlv_rAct"],
    secondary_range=(-5, 200),
)


# Registry of all V2 charts by action_id

# 🔄 How It Works:
# Snapshot Detection: System determines if loaded data is V2 format
# Registry Selection: Uses V2_CHARTS instead of V1_CHARTS or EUD_CHARTS
# UI Population: Quick chart panel shows V2-specific options
# Chart Generation: Selected chart definition builds the appropriate plot
# 💡 Example Flow:
# User loads V2 snapshot data
# Quick chart panel shows "Rail Pressure", "Misfire", "Torque Limits", etc.
# User clicks "V2_MISFIRE" → looks up in V2_CHARTS
# Gets V2_MISFIRE definition with misfire detection PIDs
# Creates status chart showing misfire flags
 
V2_CHARTS: dict[str, QuickChartDef] = {
    "V2_BATTERY_TEST": V2_BATTERY_TEST,                   # Battery Voltage vs Engine Speed
    "V2_RAIL_PRESSURE": V2_RAIL_PRESSURE,                 # Actual vs Desired Rail Pressure
    "V2_RAIL_GAP": V2_RAIL_GAP,                           # Rail Gap
    "V2_IMV_CURRENT": V2_IMV_CURRENT,                     # IMV Current
    "V2_TURBO": V2_TURBO,                                 # Manifold Pressure vs Atmospheric Pressure
    "V2_MISFIRE": V2_MISFIRE,                             # Misfire Counters
    "V2_THROTTLE_VALVE": V2_THROTTLE_VALVE,               # Throttle Valve Position
    "V2_ENGINE_LOAD": V2_ENGINE_LOAD,                     # Engine Load
    "V2_ENGINE_TORQUE_LIMITS": V2_ENGINE_TORQUE_LIMITS,   # Engine Torque Limits
    "V2_BOOST_LEAK": V2_BOOST_LEAK,                       # Boost Leak
}
