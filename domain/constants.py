from domain.snaptypes import SnapType

# Application title global
APP_TITLE = "Snapshot Decoder"
APP_VERSION = "1.0.0"

# Buttons for each snapshot type
# Button name, COMMAND NAME, tooltip
BUTTONS_BY_TYPE: dict[SnapType, list[tuple[str, str, str]]] = {
    SnapType.ECU_V1: [
        ("Battery Test", "V1_BATTERY_TEST", 
        "Battery Voltage vs RPM (Cranking voltage drop and charging voltage)"),
        ("Rail Pressure", "V1_RAIL_PRESSURE", 
        "Demand vs Actual Rail Pressure (Measured at 'steady-state' consistant fuel mg/stroke)"),
        ("Rail Gap", "V1_RAIL_GAP", 
        "Rail Pressure Gap (Greater than 2150 for 5 seconds the ECU will shut down the injectors)"),
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
}

# Mapping of raw unit strings to normalized display text
UNIT_NORMALIZATION: dict[str, str] = {
    "s": "Seconds",
    "ms": "Milliseconds",
    "rpm": "RPM",
    "adcnt": "AD Counts",
    "g": "Grams",
    "us": "Microseconds",
    "l": "Liters",
    "g/s": "Grams/Second",
    "t/f": "True(1)/False(0)",
    "false/true": "True(1)/False(0)",
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
    "counts": "AD Counts",
    "hours": "Hours",
    "min": "Minutes",
    "l(liter)": "Liter",
    "v": "Volts",
    "mg/s": "Milligrams/Second",
    "mg": "Milligrams",
    "count": "Counter",
    
    }

# Define a mapping of header PIDs to SnapType enumerations
PID_KEY = {
    "p_l_battery_raw": SnapType.ECU_V1,
    "battu_u": SnapType.ECU_V2,
    "p_l_egr_close_pos_learnt_nvv": SnapType.EUD_V1,
    
    # Add more patterns as needed
}