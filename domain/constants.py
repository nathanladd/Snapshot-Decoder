
from domain.snaptypes import SnapType

# Application title global
APP_TITLE = "Snapshot Decoder"
APP_VERSION = "1.0.0"

# Buttons for each snapshot type
# Button name, COMMAND NAME, tooltip
BUTTONS_BY_TYPE: dict[SnapType, list[tuple[str, str, str]]] = {
    SnapType.ECU_V1: [
        ("Battery Test", "V1_BATTERY_TEST", "Plot battery V vs RPM"),
        ("Rail Pressure", "V1_RAIL_PRESSURE", "Demand vs Actual + Gap"),
        
    ],
    SnapType.ECU_V2: [
        ("Battery Test", "V2_BATTERY_TEST", "Plot battery V vs RPM"),
        
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
    "program sw version": "Engine Analyzer Version",
    "data logging": "Data Logging"
}