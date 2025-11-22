from typing import List
from domain.snaptypes import SnapType
from domain.constants import BUTTONS_BY_TYPE


def apply_quick_chart_setup(main_app, snaptype: SnapType, action_id: str, primary_pids: List[str], primary_min: str = "", primary_max: str = "", secondary_pids: List[str]=[], secondary_min: str="", secondary_max: str=""):
    # Retrieve tooltip for the chart title
    tooltip = None
    if snaptype in BUTTONS_BY_TYPE:
        for button_name, cmd, tip in BUTTONS_BY_TYPE[snaptype]:
            if cmd == action_id:
                tooltip = tip
                break
    
    # Set scripted PID names for primary and secondary axes
    main_app.primary_series = primary_pids
    main_app.secondary_series = secondary_pids
    
    # Update list boxes
    main_app.primary_list.delete(0, 'end')
    for pid in main_app.primary_series:
        main_app.primary_list.insert('end', pid)
    
    main_app.secondary_list.delete(0, 'end')
    for pid in main_app.secondary_series:
        main_app.secondary_list.insert('end', pid)
    
    # Set scripted min/max values for axes
    if primary_min and primary_max:
        main_app.primary_auto.set(False)
        main_app.primary_ymin.set(primary_min)
        main_app.primary_ymax.set(primary_max)
    else:
        main_app.primary_auto.set(True)
    
    if secondary_min and secondary_max:
        main_app.secondary_auto.set(False)
        main_app.secondary_ymin.set(secondary_min)
        main_app.secondary_ymax.set(secondary_max)
    else:
        main_app.secondary_auto.set(True)
    
    # Trigger toggle to update entry states
    main_app._toggle_primary_inputs()
    main_app._toggle_secondary_inputs()
    
    # Generate the chart
    main_app.plot_combo_chart()
    
    # Set custom title if tooltip found
    if tooltip:
        main_app.ax_left.set_title(tooltip)
        # Update working_config title to match so toolbar has correct title for PDF export
        if main_app.working_config:
            main_app.working_config.title = tooltip
        main_app.canvas.draw_idle()

# ----------------------------------------------------------------------------
# ----------------------------------V1 Charts----------------------------------
# ----------------------------------------------------------------------------

def V1_show_battery_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_BATTERY_TEST",
        ["P_L_Battery_raw"],
        "0",
        "18",
        ["IN_Engine_cycle_speed"],
        "-50",
        "4000"
    )
    

def V1_show_rail_pressure_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_RAIL_PRESSURE",
        ["RPC_Rail_pressure_dmnd", "P_L_RAIL_PRES_RAW"],
        "-15",
        "30000",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )


def V1_show_rail_gap_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_RAIL_GAP",
        ["RPC_Rail_pressure_error"],
        "-5000",
        "5000",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )
    
def V1_show_imv_current_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_IMV_CURRENT",
        ["RPC_Im_crt_dmnd", "P_L_Im_crt_fb"],
        "0",
        "1050",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )

def V1_show_turbo_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_TURBO",
        ["P_L_MAP_RAW", "P_L_Atmosp_raw"],
        "-10",
        "35",
        ["IN_Engine_cycle_speed"],
        "-50",
        "6250"
    )
def V1_show_EGR_flow_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_EGR_FLOW",
        ["ACM_INTAKE_PORT_AIR_FLOW_SPD", "ACM_INTAKE_PORT_AIR_FLOW_MAF"],
        "0",
        "150",
        ["IN_Egr_position"],
        "-10",
        "400"
    )

def V1_show_EGR_position_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_EGR_POSITION",
        ["P_L_Egr_close_pos_mean_nvv", "P_L_Egr_feedback_pos_cnts"],
        "0",
        "1000",
        ["ACM_Egr_position_dmnd"],
        "-10",
        "400"
    )

def V1_show_piston_delta_chart(main_app, snaptype: SnapType):
    # Filter PIDs to only include those present in the snapshot (for 3 cylinder engine 1.8L)
    all_cylinders = ["IN_Bal_delta_speed[0]", "IN_Bal_delta_speed[1]", "IN_Bal_delta_speed[2]", "IN_Bal_delta_speed[3]"]
    cylinders_present = [pid for pid in all_cylinders if pid in main_app.engine.snapshot.columns]
    
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_PISTON_DELTA",
        cylinders_present,
        "-100",
        "100",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )

def V1_show_cam_crank_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_CAM_CRANK",
        ["P_L_aps_sync_tasks_enabled", "P_L_aps_crank_valid", "P_L_aps_cam_valid"],
        "-10",
        "4",
        ["SMC_ENGINE_STATE"],
        "-2",
        "10"
    )

def V1_show_start_aid_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_START_AID",
        ["SAC_Glow_plug_output"],
        "-10",
        "4",
        ["SMC_ENGINE_STATE"],
        "-2",
        "10"
    )

def V1_show_air_fuel_ratio_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_AIR_FUEL_RATIO",
        ["AFC_Air_fuel_ratio"],
        "-50",
        "130",
        ["T_D_Smoke_limit_active"],
        "-2",
        "10"
    )

def V1_show_torque_control_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_TORQUE_CONTROL",
        ["T_D_Actual_brake_torque", "T_D_Max_brake_torque"]
        
    )

# ----------------------------------------------------------------------------
# ----------------------------------V2 Charts----------------------------------
# ----------------------------------------------------------------------------

def V2_show_battery_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_BATTERY_TEST",
        ["BattU_u"],
        "0",
        "18000",
        ["Epm_nEng"],
        "-50",
        "3000"
    )

def V2_show_rail_pressure_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_RAIL_PRESSURE",
        ["RailP_pFlt", "Rail_pSetPoint"],
        "-15", "30000"  
    )

def V2_show_rail_gap_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_RAIL_GAP",
        ["Rail_pDvt"],
        "-50","4000"
    )

def V2_show_imv_current_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_IMV_CURRENT",
        ["MeUn_iActFlt", "MeUn_iSet"],
    )

def V2_show_turbo_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_TURBO",
        ["Air_pIntkVUs", "EnvP_p"],
        "-20",
        "35",
        ["InjCrv_qMI1Des"],
        "-5",
        "200"
    )

def V2_show_misfire_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_MISFIRE",
        ["MisfDet_ctMifMem_[0]", "MisfDet_ctMifMem_[2]", "MisfDet_ctMifMem_[3]","MisfDet_ctMifMem_[1]"],
        "-20","150"
    )

def V2_show_throttle_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_THROTTLE_VALVE",
        ["ThrVlv_r", "ThrVlv_rAct"],
        "-5",
        "140"

    )

def V2_show_load_chart(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_ENGINE_LOAD",
        ["CoETS_rTrq"],
        "-100","110",
        ["PthSet_TrqInrSet"],
        "0","800"
    )

def V2_show_engine_torque_limits(main_app, snaptype: SnapType):
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V2_ENGINE_TORQUE_LIMITS",
        ["CoETS_stCurrLimActive"]
    )
