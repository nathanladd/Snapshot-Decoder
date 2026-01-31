from domain.snaptypes import SnapType
from version import APP_VERSION

# Application title global
APP_TITLE = "Snapshot Decoder"
# Help URL
UPDATE_URL = "https://nathanladd.github.io/Snapshot-Decoder/"


# Buttons for each V1 snapshot type
# Button name, COMMAND NAME, tooltip
BUTTONS_BY_TYPE: dict[SnapType, list[tuple[str, str, str]]] = {
    SnapType.ECU_V1: [
        ("Battery Test", "V1_BATTERY_TEST", 
        "Battery Voltage vs RPM"),
        ("Rail Pressure", "V1_RAIL_PRESSURE", 
        "Demand vs Actual Rail Pressure"),
        ("Rail Gap", "V1_RAIL_GAP", 
        "Rail Pressure Gap"),
        ("IMV Current", "V1_IMV_CURRENT", 
        "IMV Current Actual vs Demand"),
        ("Turbo", "V1_TURBO", 
        "Manifold Pressure, Atmospheric Pressure, and RPM"),
        ("EGR Flow", "V1_EGR_FLOW", 
        "Mass Air Flow Sensor vs Speed Density"),
        ("EGR Position", "V1_EGR_POSITION", 
        "EGR Position vs percent Demand"),
        ("Piston Delta", "V1_PISTON_DELTA", 
        "Piston Delta Speed"),
        ("Cam/Crank", "V1_CAM_CRANK", 
        "Cam/Crank Condition with Sync"),
        ("Start Aid", "V1_START_AID", 
        "Start Aid Condition with Engine State"),
        ("Air/Fuel Ratio", "V1_AIR_FUEL_RATIO", 
        "Air/Fuel Ratio and Smoke Limit Control"),
        ("Torque Control", "V1_TORQUE_CONTROL", 
        "Actual Brake Torque vs Torque Limit"),
        ("Fuel/Coolant Temp", "V1_FUEL_COOLANT_TEMP", 
        "Fuel/Coolant Temperature")
    ],
    
# Buttons for each V2 snapshot type
# Button name, COMMAND NAME, tooltip
    SnapType.ECU_V2: [
        ("Battery Test", "V2_BATTERY_TEST", 
        "Battery Voltage vs RPM"),
        ("Rail Pressure", "V2_RAIL_PRESSURE", 
        "Demand vs Actual Rail Pressure"),
        ("Rail Gap", "V2_RAIL_GAP", 
        "Rail Pressure Gap"),
        ("IMV Current", "V2_IMV_CURRENT", 
        "IMV Current Actual vs Demand"),
        ("Turbo", "V2_TURBO", 
        "Manifold Pressure, Atmospheric Pressure, and Fuel Quantity"),
        ("Misfire", "V2_MISFIRE", 
        "Misfire Count per Cylinder"),
        ("Throttle Valve", "V2_THROTTLE_VALVE",
        "Throttle Valve Actual vs Desired"),
        ("Engine Load", "V2_ENGINE_LOAD",
        "Load Percent and Brake Torque"),
        ("Torque Limits", "V2_ENGINE_TORQUE_LIMITS",
        "Torque Limits"),
        ("Fuel/Coolant Temp", "V2_FUEL_COOLANT_TEMP", 
        "Fuel/Coolant Temperature")
        
    ],
    SnapType.DCU_V1: [
        
    ],
    SnapType.EUD_V1: [
        ("Speed/Load", "V1EUD_SPEED_V_LOAD", "Speed vs Load"),
        ("Speed Band", "V1EUD_SPEED_BAND", "Speed Band"),
        ("Elevation", "V1EUD_ELEVATION", "Elevation"),
        ("EGT", "V1EUD_EGT", "Exhaust Gas Temperature")
        
    ],
    SnapType.EUD_V2: [
        
    ],
}

# Standardize the labels found in the header. 
# - labels we expect in row 0..3 of collumn 0, with values in collumn 1.
# squeez and clean the name from the snapshot cell and map it to a more readable name
HEADER_LABELS = {
    "engine model": "Engine Model",
    "ecu map version": "ECU Map Version",
    "program sw version": "Engine Analyzer",
    "data logging": "Date / Time",
    "engine no": "Engine Model",
    "sw version": "Engine Analyzer",
    "ecu map": "Map Version",
    "start time": "Date / Time",
}

# Mapping of raw unit strings to normalized display text
UNIT_NORMALIZATION: dict[str, str] = {
    "s": "Seconds",
    "ms": "Milliseconds",
    "rpm": "RPM",
    "adcnt": "Analog/Digital Counts",
    "g": "Grams",
    "us": "Microseconds",
    "l": "Liters",
    "g/s": "Grams/Second",
    "t/f": "[0]False  [1]True",
    "false/true": "[0]False  [1]True",
    "%": "Percent",
    "deg c": "Celsius",
    "deg f": "Fahrenheit",
    "ma": "Milliamps",
    "mv": "Millivolts",
    "nm": "Newton Meters",
    "edeg": "Crankshaft Angle",
    "psi": "PSI",
    "ppm": "Parts/Million",
    "deg crs": "Crankshaft Angle",
    "mg/str": "Milligrams/Stroke",
    "kg/h": "Kilograms/Hour",
    "m^3/h": "Cubic Meters/Hour",
    "mg/s": "Milligrams/Second",
    "mm": "Millimeters",
    "counts": "Analog/Digital Counts",
    "hours": "Hours",
    "min": "Minutes",
    "l(liter)": "Liter",
    "v": "Volts",
    "mg/s": "Milligrams/Second",
    "mg": "Milligrams",
    "count": "Counter",
    "mg/stroke": "Milligrams/Stroke",
    "kpa": "Kilopascals",
    "bar": "Barometric Pressure",
    
    }

# Define PIDs that identify each snapshot type (SnapType → list of identifying PIDs)
# Detection will match if ANY of the listed PIDs are found in the header row
SNAPSHOT_TYPE_PIDS: dict[SnapType, list[str]] = {
    SnapType.ECU_V1: [
        "p_l_battery_raw",
        "p_l_atmosp_raw",
        "smc_engine_state",
        "in_engine_cycle_speed",
        "in_pedal_position",
        "acm_intake_port_air_flow_maf",
    ],
    SnapType.ECU_V2: [
        "battu_u",
        "epm_neng",
        "afsdm",
        "air_pintkvus",
        "app_r",
        "coets_stcurrlimactive",
    ],
    SnapType.EUD_V1: [
        "p_l_egr_close_pos_learnt_nvv",
        "eud_atmos_pres_timer_nvv[1]",
        "eud_engine_idle_time_nvv",
        "i_c_mdp_correction_dat_i_0",
    ],
}

# Define PIDs that identify specific engine systems
# Detection will match if ANY of the listed PIDs are found in the snapshot
SYSTEM_PIDS: dict[str, list[str]] = {
    "egr": [
        "ACM_Egr_position_dmnd", #ECU_V1
        "IN_Egr_position", #ECU_V1
        "egrvlv_ract", #ECU_V2
        "egrvlv_r", #ECU_V2
    ],
    "doc": [
        "exh_tadaptoxicatus", #ECU_V2
        "exh_urawtoxicatus", #ECU_V2
    ],
    "dpf": [
        "Exh_pPFltDiff", #ECU_V2
    ],
    "scr": [
        "scr_pupmpp", #ECU_V2
        "P_T_Dpf_model_soot_mass_nvv", #ECU_V1 (SCR PIDs in V1 seem to be labeled DPF)
    ],
    "air_throttle": [
        "ThrVlv_rAct", #ECU_V2
        "P_L_Thrtl_feedback_abs_pos", #ECU_V1 (currently G70 only)
    ],
    # "turbo": [
    #     "p_l_boost_pres_raw",
    #     "boost_pboostact",
    #     "boost_pboostdes",
    # ],
}

# Map snapshot types to their engine hours column names
ENGINE_HOURS_COLUMNS = {
    SnapType.ECU_V1: "EUD_Engine_run_time_total_nvv",
    SnapType.ECU_V2: "EngDa_tiEngOn",
    SnapType.EUD_V1: "EUD_Engine_run_time_total_nvv",
    # Add more snapshot types and their column names as needed
    # SnapType.ECU_V2: "column_name_for_v2",
}