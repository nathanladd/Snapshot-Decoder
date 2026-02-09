"""
Reference chart definitions for V2 architecture.

These charts provide reference/baseline data for comparison with current snapshots.
"""

from domain.quick_charts.definitions import QuickChartDef
from domain.snaptypes import SnapType

# Reference chart definitions for ECU V2
REFERENCE_CHARTS: dict[str, QuickChartDef] = {
    "REF_ENGINE_SPEED": QuickChartDef(
        action_id="REF_ENGINE_SPEED",
        title="Engine Speed",
        primary_pids=["Epm_nEng"]
    ),
    
    "REF_TPS": QuickChartDef(
        action_id="REF_TPS", 
        title="TPS",
        primary_pids=["APP_r"]
    ),
    
    "REF_TORQUE": QuickChartDef(
        action_id="REF_TORQUE",
        title="Torque", 
        primary_pids=["PthSet_TrqInrSet"]
    ),
    
    "REF_FUEL_COOLANT_TEMP": QuickChartDef(
        action_id="REF_FUEL_COOLANT_TEMP",
        title="Fuel and Coolant",
        primary_pids=["FuelT_t", "CEngDsT_t"],
        primary_range=(-20, 250),
    ),
    
    "REF_AIR_TEMP": QuickChartDef(
        action_id="REF_AIR_TEMP",
        title="Air Temperature",
        primary_pids=["Air_tAFS"],
        primary_range=(-20, 110),
    ),
    
    "REF_OIL_TEMP": QuickChartDef(
        action_id="REF_OIL_TEMP",
        title="Oil Temperature",
        primary_pids=["Oil_tSwmp"],
        primary_range=(-20, 250),
    ),
    
    "REF_RAIL_PRESSURE": QuickChartDef(
        action_id="REF_RAIL_PRESSURE",
        title="Rail Pressure",
        primary_pids=["RailP_pFlt", "Rail_pSetPoint"],
    ),
    
    "REF_IMV_CURRENT": QuickChartDef(
        action_id="REF_IMV_CURRENT",
        title="IMV Current",
        primary_pids=["MeUn_iActFlt", "MeUn_iSet"],
    ),
    
    "REF_FUEL_QUANTITY": QuickChartDef(
        action_id="REF_FUEL_QUANTITY",
        title="Fuel Quantity",
        # The pre-injection PID names get corrected if they have an underscore in front of the [0]
        primary_pids=["InjCrv_qMI1Des", "InjCrv_qPiI1Des[0]", "InjCrv_qPiI2Des[0]", "InjCrv_qPiI3Des[0]"],
    ),
    
    "REF_MAF": QuickChartDef(
        action_id="REF_MAF",
        title="MAF",
        primary_pids=["AFS_dm", "AirMod_mfGasIntkVlv_f"],
    ),
    
    "REF_MAP": QuickChartDef(
        action_id="REF_MAP",
        title="MAP",
        primary_pids=["Air_pIntkVUs", "EnvP_p"],
    ),
    
    "REF_EGR_POSITION": QuickChartDef(
        action_id="REF_EGR_POSITION",
        title="EGR Position",
        primary_pids=["EGRVlv_rAct", "EGRVlv_r"],
        primary_range=(-10, 110),
    ),
    
    "REF_OIL_PRESSURE": QuickChartDef(
        action_id="REF_OIL_PRESSURE",
        title="Oil Pressure",
        primary_pids=["Oil_pSwmp"],
    ),
}
