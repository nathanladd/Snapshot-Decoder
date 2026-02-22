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
        ("EGR Position", "V1_EGR_POSITION", 
        "EGR Position vs percent Demand"),
        ("Piston Delta", "V1_PISTON_DELTA", 
        "Piston Delta Speed"),
        ("Cam/Crank", "V1_CAM_CRANK", 
        "Cam/Crank Condition with Sync"),
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
        "P_T_Dpf_model_soot_mass_nvv", #ECU_V1 (SCR PIDs in V1 seem to be labeled DPF)
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

