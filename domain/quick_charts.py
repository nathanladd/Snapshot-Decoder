from typing import List
from domain.snaptypes import SnapType
from domain.constants import BUTTONS_BY_TYPE


def apply_quick_chart_setup(main_app, snaptype: SnapType, action_id: str, primary_pids: List[str], primary_min: str, primary_max: str, secondary_pids: List[str]=[], secondary_min: str="", secondary_max: str=""):
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
    main_app.primary_auto.set(False)
    main_app.primary_ymin.set(primary_min)
    main_app.primary_ymax.set(primary_max)
    
    main_app.secondary_auto.set(False)
    main_app.secondary_ymin.set(secondary_min)
    main_app.secondary_ymax.set(secondary_max)
    
    # Trigger toggle to update entry states
    main_app._toggle_primary_inputs()
    main_app._toggle_secondary_inputs()
    
    # Generate the chart
    main_app.plot_combo_chart()
    
    # Set custom title if tooltip found
    if tooltip:
        main_app.ax_left.set_title(tooltip)
        main_app.canvas.draw_idle()

# ----------------------------------V1 Charts----------------------------------

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
        "1050"
        
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
    apply_quick_chart_setup(
        main_app,
        snaptype,
        "V1_PISTON_DELTA",
        ["IN_Bal_delta_speed[0]", "IN_Bal_delta_speed[1]", "IN_Bal_delta_speed[2]", "IN_Bal_delta_speed[3]"],
        "-100",
        "100",
        ["FQD_Chkd_inj_fuel_dmnd"],
        "-5",
        "300"
    )
# ----------------------------------V2 Charts----------------------------------

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