"""
Reference chart definitions for V2 architecture.

Declarative definitions for reference charts that can be used both
for individual chart display and PDF generation.
"""

from dataclasses import dataclass
from typing import List
from .definitions import QuickChartDef
from domain.snaptypes import SnapType


@dataclass
class ReferenceChartPage:
    """Defines a page of reference charts."""
    title: str
    charts: List[QuickChartDef]


# Reference chart definitions using existing QuickChartDef structure
REFERENCE_PAGES = [
    ReferenceChartPage(
        title="Operating Conditions",
        charts=[
            QuickChartDef(
                action_id="REF_ENGINE_SPEED",
                title="Engine Speed",
                primary_pids=["Epm_nEng"]
            ),
            QuickChartDef(
                action_id="REF_TPS", 
                title="TPS",
                primary_pids=["APP_r"]
            ),
            QuickChartDef(
                action_id="REF_TORQUE",
                title="Torque", 
                primary_pids=["PthSet_TrqInrSet"]
            )
        ]
    ),
    
    ReferenceChartPage(
        title="Temperatures",
        charts=[
            QuickChartDef(
                action_id="REF_FUEL_COOLANT_TEMP",
                title="Fuel and Coolant",
                primary_pids=["FuelT_t", "CEngDsT_t"],
                primary_range=(-20, 250),
            ),
            QuickChartDef(
                action_id="REF_AIR_TEMP",
                title="Air Temperature",
                primary_pids=["Air_tAFS"],
                primary_range=(-20, 110),
            ),
            QuickChartDef(
                action_id="REF_OIL_TEMP",
                title="Oil Temperature",
                primary_pids=["Oil_tSwmp"],
                primary_range=(-20, 250),
            )
        ]
    ),
    
    ReferenceChartPage(
        title="Fuel System",
        charts=[
            QuickChartDef(
                action_id="REF_RAIL_PRESSURE",
                title="Rail Pressure",
                primary_pids=["RailP_pFlt", "Rail_pSetPoint"],
            ),
            QuickChartDef(
                action_id="REF_IMV_CURRENT",
                title="IMV Current",
                primary_pids=["MeUn_iActFlt", "MeUn_iSet"],
            ),
            QuickChartDef(
                action_id="REF_FUEL_QUANTITY",
                title="Fuel Quantity",
                # The pre-injection PID names get corrected if they have an underscore in front of the [0]
                primary_pids=["InjCrv_qMI1Des", "InjCrv_qPiI1Des[0]", "InjCrv_qPiI2Des[0]", "InjCrv_qPiI3Des[0]"],
            )
        ]
    ),
    
    ReferenceChartPage(
        title="Air Circuit",
        charts=[
            QuickChartDef(
                action_id="REF_MAF",
                title="MAF",
                primary_pids=["AFS_dm", "AirMod_mfGasIntkVlv_f"],
            ),
            QuickChartDef(
                action_id="REF_MAP",
                title="MAP",
                primary_pids=["Air_pIntkVUs", "EnvP_p"],
            ),
            QuickChartDef(
                action_id="REF_EGR_POSITION",
                title="EGR Position",
                primary_pids=["EGRVlv_rAct", "EGRVlv_r"],
                primary_range=(-10, 110),
            )
        ]
    ),
    
    ReferenceChartPage(
        title="Oil Pressure",
        charts=[
            QuickChartDef(
                action_id="REF_OIL_PRESSURE",
                title="Oil Pressure",
                primary_pids=["Oil_pSwmp"],
            )
        ]
    )
]

# Mapping of snapshot types to their reference pages
REFERENCE_CHARTS_BY_TYPE = {
    SnapType.ECU_V2: REFERENCE_PAGES,
}
