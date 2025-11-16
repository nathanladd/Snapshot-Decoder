from domain.snaptypes import SnapType

# Application title global
APP_TITLE = "Snapshot Decoder"
APP_VERSION = "1.0.0"

# Buttons for each snapshot type
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
        "Cam/Crank Condition with Engine State"),
    ],
    SnapType.ECU_V2: [
        ("Battery Test", "V2_BATTERY_TEST", "Battery V vs RPM"),
        
    ],
    SnapType.DCU_V1: [
        
    ],
    SnapType.EUD_V1: [
        
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
}

# Mapping of raw unit strings to normalized display text
UNIT_NORMALIZATION: dict[str, str] = {
    "s": "Seconds",
    "ms": "Milliseconds",
    "rpm": "RPM",
    "adcnt": "Analog to Digital Counts",
    "g": "Grams",
    "us": "Microseconds",
    "l": "Liters",
    "g/s": "Grams/Second",
    "t/f": "[1]True | [0]False",
    "false/true": "[1]True | [0]False",
    "%": "Percent",
    "deg c": "Degrees Celsius",
    "deg f": "Degrees Fahrenheit",
    "ma": "Milliamps",
    "mv": "Millivolts",
    "nm": "Newton Meters",
    "edeg": "Crankshaft Angle",
    "psi": "PSI",
    "ppm": "Parts Per Million",
    "deg crs": "Crankshaft Angle",
    "mg/str": "Milligrams/Stroke",
    "kg/h": "Kilograms/Hour",
    "m^3/h": "Cubic Meters/Hour",
    "mg/s": "Milligrams/Second",
    "mm": "Millimeters",
    "counts": "Analog to Digital Counts",
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

# Define a mapping of header PIDs to SnapType enumerations
PID_KEY = {
    "p_l_battery_raw": SnapType.ECU_V1,
    "battu_u": SnapType.ECU_V2,
    "p_l_egr_close_pos_learnt_nvv": SnapType.EUD_V1,
    
    # Add more patterns as needed
}

# Map snapshot types to their engine hours column names
ENGINE_HOURS_COLUMNS = {
    SnapType.ECU_V1: "EUD_Engine_run_time_total_nvv",
    SnapType.ECU_V2: "EngDa_tiEngOn",
    # Add more snapshot types and their column names as needed
    # SnapType.ECU_V2: "column_name_for_v2",
}