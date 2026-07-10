from domain.snaptypes import SnapType
from version import APP_VERSION

# Application title global
APP_TITLE = "Snapshot Decoder"
# Help URL
UPDATE_URL = "https://nathanladd.github.io/Snapshot-Decoder/"

# Map snapshot types to their engine hours column names
ENGINE_HOURS_COLUMNS = {
    SnapType.ECU_V1: "EUD_Engine_run_time_total_nvv",
    SnapType.ECU_V2: "EngDa_tiEngOn",
    SnapType.EUD_V1: "EUD_Engine_run_time_total_nvv",
    SnapType.DCU_V1: "EngDa_tiEngOn",
    # Add more snapshot types and their column names as needed
    # SnapType.ECU_V2: "column_name_for_v2",
}

#################################################################################################################################
########################################### Quick Chart V1_ECU ##################################################################
#################################################################################################################################

#                           Format: Button name, COMMAND NAME, tooltip

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
        ("EGR Calibration", "V1_EGR_CALIBRATION", 
        "EGR Position vs learned closed position"),
        ("Piston Delta", "V1_PISTON_DELTA", 
        "Piston Delta Speed"),
        ("Torque", "V1_TORQUE_CONTROL", 
        "Actual Brake Torque vs Torque Limit"),
    ],

########################################################################################################################################
############################################### Quick Charts V2_ECU ##################################################################
########################################################################################################################################

#                                      Format:Button name, COMMAND NAME, tooltip
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
        ("EGR Flow", "V2_EGR_FLOW",
        "Mass Air Flow Sensor vs Speed Density"),
        
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


# Canonical live metrics shown in compact slider live widgets.
LIVE_METRIC_KEYS: tuple[str, ...] = (
    "ENGINE_SPEED",
    "OIL_TEMP",
    "OIL_PRESSURE",
    "COOLANT_TEMP",
    "CHECK_ENGINE",
    "ENGINE_STATE",          #ECU_V1 Engines
    "ENGINE_STATUS",         #ECU_V2 Engines
    "SYNC_STATUS",           #ECU_V2 Crank/Cam Sync
    "START_AID",
    "SMOKE_LIMIT",
    "OIL_PRESSURE_LAMP",
    "CAM_VALID",
    "SYNC_TASKS",
    "CRANK_VALID",
)

# Per-snapshot PID alias map for each canonical live metric.
# Strict opt-in: only snapshot types defined here will show compact gauges/chips.
LIVE_METRIC_PID_MAP: dict[SnapType, dict[str, list[str]]] = {
    SnapType.ECU_V1: {
        "ENGINE_SPEED": ["IN_Engine_cycle_speed"],
        "OIL_TEMP": ["P_L_Oil_temperature"],
        "OIL_PRESSURE": ["P_L_Oil_pressure"],
        "COOLANT_TEMP": ["P_L_Coolant_temperature"],
        "CHECK_ENGINE": ["ICI_Ce_lamp_output"],
        "ENGINE_STATE": ["SMC_Engine_state"],                 #ECU_V1 Engines
        "START_AID": ["SAC_Glow_plug_output"],
        "SMOKE_LIMIT": ["T_D_Smoke_limit_active"],
        "OIL_PRESSURE_LAMP": ["ICI_Oil_pressure_lamp_output"],
        "CAM_VALID": ["P_L_aps_cam_valid"],
        "SYNC_TASKS": ["P_L_aps_sync_tasks_enabled"],
        "CRANK_VALID": ["P_L_aps_crank_valid"],
    },
    SnapType.ECU_V2: {
        "ENGINE_SPEED": ["Epm_nEng"],
        "OIL_TEMP": ["Oil_tSwmp"],
        "OIL_PRESSURE": ["Oil_pSwmp"],
        "COOLANT_TEMP": ["CEngDsT_t"],
        "ENGINE_STATUS": ["CoEng_st"],                         #ECU_V2 Engines
        "SYNC_STATUS": ["Epm_stSync"],                          #ECU_V2 Crank/Cam Sync
    },
}

# Display metadata for compact live metrics.
LIVE_METRIC_META: dict[str, dict[str, object]] = {
    "ENGINE_SPEED": {"label": "RPM", "unit": "RPM", "min": 0, "max": 3500, "decimals": 0},
    "OIL_TEMP": {"label": "Oil", "unit": "°C", "min": -40, "max": 180, "decimals": 0},
    "OIL_PRESSURE": {"label": "Oil", "unit": "PSI", "min": 0, "max": 120, "decimals": 0},
    "COOLANT_TEMP": {"label": "Coolant", "unit": "°C", "min": -40, "max": 140, "decimals": 0},
    "CHECK_ENGINE": {"label": "Check Engine", "unit": "", "min": 0, "max": 1, "decimals": 0},
    "ENGINE_STATE": {"label": "Engine State", "unit": "", "min": 0, "max": 5, "decimals": 0},
    "ENGINE_STATUS": {"label": "Engine Status", "unit": "", "min": 0, "max": 5, "decimals": 0},
    "SYNC_STATUS": {"label": "Sync Status", "unit": "", "min": 0, "max": 30, "decimals": 0},
    "START_AID": {"label": "Start Aid", "unit": "", "min": 0, "max": 1, "decimals": 0},
    "SMOKE_LIMIT": {"label": "Smoke Limit", "unit": "", "min": 0, "max": 1, "decimals": 0},
    "OIL_PRESSURE_LAMP": {"label": "Oil Pressure", "unit": "", "min": 0, "max": 1, "decimals": 0},
    "CAM_VALID": {"label": "Cam", "unit": "", "min": 0, "max": 1, "decimals": 0},
    "SYNC_TASKS": {"label": "Sync", "unit": "", "min": 0, "max": 1, "decimals": 0},
    "CRANK_VALID": {"label": "Crank", "unit": "", "min": 0, "max": 1, "decimals": 0},
}

# Optional state labels for chip-based metrics.
LIVE_METRIC_STATE_LABELS: dict[SnapType, dict[str, dict[int, str]]] = {
    SnapType.ECU_V1: {
        "CHECK_ENGINE": {0: "Off", 1: "On"},
        "START_AID": {0: "Off", 1: "On"},
        "SMOKE_LIMIT": {0: "Off", 1: "On"},
        "OIL_PRESSURE_LAMP": {0: "Off", 1: "On"},
        "ENGINE_STATE": {0: "Stopped", 1: "Cranking", 2: "Running", 3: "Stalling"},
    },
    SnapType.ECU_V2: {
        "ENGINE_STATUS": {
            0: "STANDBY",
            1: "READY",
            2: "CRANKING",
            3: "RUNNING",
            4: "STOPPING",
            5: "FINISH",
        },
        "SYNC_STATUS": {
            0: "EPM_NO_SYNC",
            10: "EPM_ALE_SYNC",
            20: "EPM_CAS_SYNC",
            21: "EPM_DIRSTALE_SYNC",
            30: "EPM_FULL_SYNC",
        },
    },
}

# Reference chart mappings for V2 architecture
REFERENCE_CHARTS_BY_TYPE = {
    SnapType.ECU_V2: [
        ("Generate Reference PDF...", "REF_GENERATE_PDF", "Generate complete reference charts PDF"),
        ("Ref: Engine Speed", "REF_ENGINE_SPEED", "Reference Engine Speed"),
        ("Ref: TPS", "REF_TPS", "Reference Throttle Position"),
        ("Ref: Torque", "REF_TORQUE", "Reference Torque"),
        ("Ref: Fuel/Coolant Temp", "REF_FUEL_COOLANT_TEMP", "Reference Fuel and Coolant Temperature"),
        ("Ref: Air Temp", "REF_AIR_TEMP", "Reference Air Temperature"),
        ("Ref: Oil Temp", "REF_OIL_TEMP", "Reference Oil Temperature"),
        ("Ref: Rail Pressure", "REF_RAIL_PRESSURE", "Reference Rail Pressure"),
        ("Ref: IMV Current", "REF_IMV_CURRENT", "Reference IMV Current"),
        ("Ref: Fuel Quantity", "REF_FUEL_QUANTITY", "Reference Fuel Quantity"),
        ("Ref: MAF", "REF_MAF", "Reference Mass Air Flow"),
        ("Ref: MAP", "REF_MAP", "Reference Manifold Pressure"),
        ("Ref: EGR Position", "REF_EGR_POSITION", "Reference EGR Position"),
        ("Ref: Oil Pressure", "REF_OIL_PRESSURE", "Reference Oil Pressure"),
    ]
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
    "ecu map": "ECU Map Version",
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
    "hpa": "Hectopascals",
    "k": "Kelvin",
    }

# Override descriptions for specific PIDs during extraction.
# Applied in domain/snapshot/pid_extractor.py: when a PID matches a key here, the
# description read from the snapshot file is REPLACED with this text (always wins).
# Keys are the PID name LOWERCASED; matching is case-insensitive (mirrors
# UNIT_NORMALIZATION). Add entries here to give cryptic raw PID names a clear,
# human-readable description in the PID panel, charts, and tooltips.
PID_DESCRIPTION_OVERRIDES: dict[str, str] = {
    # Misfire-detection per-cylinder memory counters (V2). NOTE: confirm the
    # index->cylinder mapping before relying on these labels.
    "misfdet_ctmifmem_[0]": "Misfire Count - Cylinder 1",
    "misfdet_ctmifmem_[1]": "Misfire Count - Cylinder 2",
    "misfdet_ctmifmem_[2]": "Misfire Count - Cylinder 3",
    "misfdet_ctmifmem_[3]": "Misfire Count - Cylinder 4",
    }

# Conversion rules for standardizing metric units to US units.
# Key: normalized source unit string (from UNIT_NORMALIZATION values)
# Value: (target_unit, factor, pre_offset, post_offset)
# Formula: result = (value + pre_offset) * factor + post_offset
US_UNIT_CONVERSIONS: dict[str, tuple[str, float, float, float]] = {
    # Temperature → Fahrenheit
    "Celsius":              ("Fahrenheit", 1.8,      0.0,      32.0),
    "Kelvin":               ("Fahrenheit", 1.8,      -273.15,  32.0),
    # Pressure → PSI
    "Kilopascals":          ("PSI",        0.145038, 0.0,      0.0),
    "Barometric Pressure":  ("PSI",        14.5038,  0.0,      0.0),
    "Hectopascals":         ("PSI",        0.0145038, 0.0,     0.0),
    # Voltage → Volts
    "Millivolts":           ("Volts",      0.001,    0.0,      0.0),
}

# Display decimal places per unit string. Default is 2 if not listed.
UNIT_DISPLAY_DECIMALS: dict[str, int] = {
    "Volts": 3,
}

#############################################################################################################################
########################################### Snapshot Type Detectors #########################################################
#############################################################################################################################

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
        "EUD_Engine_idle_time_nvv",
        "EUD_Engine_run_time_spdbnd1_nvv",
        "EUD_Inlet_air_flow_timer_nvv[0]",
        "EUD_Rail_pressure_1_time_nvv",
    ],
    SnapType.EUD_V2: [
       "FlSys_volFlConsTot",
       "GlbDa_D2Tmr_mp[0]",
       "GlbDa_D1Tmr_mp[0]",
       "GlbDa_SingleRngTmr_mp[0]",
       "GlbDa_EventCounter_mp[0]",
       "GlbDa_MinMax_mp[0]",
       "EngDa_tiEngOp1_mp[0]",
       "EngDa_tiEngOp2_mp[0]",
       "EngDa_tiEngOp3_mp[0]",
    ],
}


#############################################################################################################################
########################################### System Detectors ################################################################
#############################################################################################################################

# Define PIDs that identify specific engine systems
# Detection will match if ANY of the listed PIDs are found in the snapshot

SYSTEM_PIDS: dict[str, list[str]] = {
    "egr": [
        "ACM_Egr_position_dmnd",       #ECU_V1
        "IN_Egr_position",             #ECU_V1
        "egrvlv_ract",                 #ECU_V2
        "egrvlv_r",                    #ECU_V2
    ],
    "doc": [
        "exh_tadaptoxicatus",          #ECU_V2
        "exh_urawtoxicatus",           #ECU_V2
        "TSE_Doc_in_temp",             #ECU_V1
    ],
    "dpf": [
        "Exh_pPFltDiff",               #ECU_V2
    ],
    "scr": [
        "scr_pupmpp",                  #ECU_V2
    ],
    "air_throttle": [
        "ThrVlv_rAct",                 #ECU_V2
    ],
    "mdp": [
        "I_C_Mdp_nb_update_success_nvv",   # MDP success counter
        "I_C_Mdp_nb_update_failure_nvv",   # MDP failure counter
        "i_c_mdp_correction_dat_i_0",      # MDP correction data (EUD_V1)
    ],
}

# V1 SCR identification via inlet/outlet temperature comparison.
# V1 snapshots expose SCR PIDs wether there is actually an SCR or not. An engine 
# with a real SCR shows inlet and outlet temps that diverge as the SCR operates, 
# while an engine without SCR has them pegged at the same value.
#cdetect_scr_by_temperature() reads these and
# turns the SCR system on when the temps differ on a high fraction of rows.

V1_SCR_TEMP_PIDS: dict[str, str] = {
    "inlet": "TSE_Dpf_in_temp",        # SCR inlet temperature (ECU_V1)
    "outlet": "TSE_Dpf_out_temp",      # SCR outlet temperature (ECU_V1)
}

# Fraction of valid rows (both temps present) where temps are "different" (as
# defined by V1_SCR_TEMP_DIFF_MIN_PCT below) required to conclude a real SCR is
# fitted. 0.95 cleanly separates studied examples: the no-SCR 740 stayed
# identical while the SCR-equipped 770 differed on essentially every row.
V1_SCR_DIFF_THRESHOLD: float = 0.50

# Minimum relative difference between inlet and outlet temps for a row to count
# as "different". |inlet - outlet| / avg(inlet, outlet) must exceed this value.
# 5% filters out sensor noise while remaining well below the 20-100F spreads
# seen on a real SCR (550-600F range → ~3-17% spread).
V1_SCR_TEMP_DIFF_MIN_PCT: float = 0.05

# Fallback signal: some real-SCR 770s keep inlet and outlet within 5% of each
# other (so the divergence test above fails), yet the pair still heats up and
# cools down over the run. If the paired temperature swings across the snapshot
# by at least this fraction ((max - min) / mean), the SCR is real. A no-SCR
# engine sits pegged at a constant temperature (≈0% swing).
V1_SCR_TEMP_SWING_MIN_PCT: float = 0.10

