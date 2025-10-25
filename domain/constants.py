
from domain.snaptypes import SnapType


APP_TITLE = "Snapshot Decoder"


BUTTONS_BY_TYPE: dict[SnapType, list[tuple[str, str, str]]] = {
    SnapType.ECU_V1: [
        ("Battery Test", "battery_test", "Plot battery V vs RPM"),
        ("Rail Pressure", "rail_pressure", "Demand vs Actual + Gap"),
        ("IMV Test", "imv_test", "Demand vs Feedback"),
        ("Injector Balance", "inj_balance", "Delta speed per cylinder"),
        ("Start Health", "start_health", "Cranking RPM, V, rail build"),
    ],
    SnapType.ECU_V2: [
        ("Start Health", "start_health", "Cranking RPM, V, rail build"),
        ("Boost Check", "boost_check", "MAP vs Atmosphere"),
        ("EGR Position", "egr_position", "Cmd vs Feedback"),
    ],
    SnapType.DCU_V1: [
        ("Usage Summary", "usage_summary", "Key hours, PTO, load"),
        ("Min/Max Chart", "minmax_chart", "Voltage & RPM extremes"),
    ],
    SnapType.EUD_V1: [
        ("I/O Monitor", "io_monitor", "Digital/analog channels"),
        ("Fault Timeline", "fault_timeline", "DTCs over time"),
    ],
}

# Standardize the labels found in the header. - labels we expect in row 0..3, col 0, with values in col 1.
HEADER_LABELS = {
    "engine model": "Engine Model",
    "ecu map version": "ECU Map Version",
    "program sw version": "Program SW Version",
    "data logging": "Data Logging"
}