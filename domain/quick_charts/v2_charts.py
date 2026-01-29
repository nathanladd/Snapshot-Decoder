"""
V2 ECU quick chart definitions.

These are declarative definitions for charts available when
viewing V2 ECU snapshot data.
"""

from domain.quick_charts.definitions import QuickChartDef, StatusChartDef


V2_BATTERY_TEST = QuickChartDef(
    action_id="V2_BATTERY_TEST",
    title="Battery Voltage vs RPM",
    primary_pids=["BattU_u"],
    primary_range=(0, 18),
    secondary_pids=["Epm_nEng"],
    secondary_range=(-50, 3000),
)

V2_FUEL_COOLANT_TEMP = QuickChartDef(
    action_id="V2_FUEL_COOLANT_TEMP",
    title="Fuel & Coolant Temperature",
    primary_pids=["CEngDsT_t", "FuelT_t"],
    primary_range=(-40, 290),
    secondary_pids=["CEngDsT_uRaw", "FuelT_uRaw"],
    secondary_range=(0, 5000),
)

V2_RAIL_PRESSURE = QuickChartDef(
    action_id="V2_RAIL_PRESSURE",
    title="Rail Pressure",
    primary_pids=["RailP_pFlt", "Rail_pSetPoint"],
    primary_range=(-15, 30000),
)

V2_RAIL_GAP = QuickChartDef(
    action_id="V2_RAIL_GAP",
    title="Rail Pressure Deviation",
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
    title="Turbo / Boost Pressure",
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
    primary_range=(-20, 150),
)

V2_THROTTLE_VALVE = QuickChartDef(
    action_id="V2_THROTTLE_VALVE",
    title="Throttle Valve Position",
    primary_pids=["ThrVlv_r", "ThrVlv_rAct"],
    primary_range=(-5, 140),
)

V2_ENGINE_LOAD = QuickChartDef(
    action_id="V2_ENGINE_LOAD",
    title="Engine Load",
    primary_pids=["CoETS_rTrq"],
    primary_range=(-100, 110),
    secondary_pids=["PthSet_TrqInrSet"],
    secondary_range=(0, 800),
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


# Registry of all V2 charts by action_id
V2_CHARTS: dict[str, QuickChartDef] = {
    "V2_BATTERY_TEST": V2_BATTERY_TEST,
    "V2_FUEL_COOLANT_TEMP": V2_FUEL_COOLANT_TEMP,
    "V2_RAIL_PRESSURE": V2_RAIL_PRESSURE,
    "V2_RAIL_GAP": V2_RAIL_GAP,
    "V2_IMV_CURRENT": V2_IMV_CURRENT,
    "V2_TURBO": V2_TURBO,
    "V2_MISFIRE": V2_MISFIRE,
    "V2_THROTTLE_VALVE": V2_THROTTLE_VALVE,
    "V2_ENGINE_LOAD": V2_ENGINE_LOAD,
    "V2_ENGINE_TORQUE_LIMITS": V2_ENGINE_TORQUE_LIMITS,
}
