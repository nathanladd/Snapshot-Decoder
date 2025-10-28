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
        "3000"
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
