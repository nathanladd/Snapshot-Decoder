"""
EUD (Engine Usage Data) quick chart definitions.

These are declarative definitions for charts available when
viewing EUD snapshot data. EUD charts typically show aggregated
statistics like speed bands, elevation time, etc.
"""

from domain.quick_charts.definitions import QuickChartDef, BarChartDef, BubbleChartDef


V1EUD_SPEED_V_LOAD = BubbleChartDef(
    action_id="V1EUD_SPEED_V_LOAD",
    title="Speed vs Load Distribution",
    primary_pids=[],  # Data is generated from column pattern
    chart_type="bubble",
    x_label="Engine Speed (RPM)",
    y_label="Load (%)",
    size_label="% of Run Time",
    column_pattern="EUD_Spdload_blm_timer_nvv[{x},{y}]",
    total_reference_column="EUD_Engine_run_time_total_nvv",
    # Speed mapping: index -> RPM (0=900, 1=1100, 2=1300, etc.)
    x_index_map={i: 900 + (i * 200) for i in range(16)},
    # Load mapping: index -> percent (0=5%, 1=15%, 2=25%, etc.)
    y_index_map={i: 5 + (i * 10) for i in range(11)},
)

V1EUD_SPEED_BAND = BarChartDef(
    action_id="V1EUD_SPEED_BAND",
    title="Speed Band Run Time",
    primary_pids=[],  # Data is generated from source_columns
    chart_type="bar",
    source_columns=[
        "EUD_Engine_run_time_spdbnd1_nvv",
        "EUD_Engine_run_time_spdbnd2_nvv",
        "EUD_Engine_run_time_spdbnd3_nvv",
        "EUD_Engine_run_time_spdbnd4_nvv",
        "EUD_Engine_run_time_spdbnd5_nvv",
    ],
    bar_labels=["< 1250", "1250-1600", "1600-2000", "2000-2400", "> 2400"],
    x_label="Speed Band",
    y_label="Hours",
    convert_seconds_to_hours=True,
)

V1EUD_ELEVATION = BarChartDef(
    action_id="V1EUD_ELEVATION",
    title="Time at Elevation",
    primary_pids=[],
    chart_type="bar",
    source_columns=[
        "EUD_Atmos_pres_timer_nvv[7]",
        "EUD_Atmos_pres_timer_nvv[6]",
        "EUD_Atmos_pres_timer_nvv[5]",
        "EUD_Atmos_pres_timer_nvv[4]",
        "EUD_Atmos_pres_timer_nvv[3]",
        "EUD_Atmos_pres_timer_nvv[2]",
        "EUD_Atmos_pres_timer_nvv[1]",
        "EUD_Atmos_pres_timer_nvv[0]",
    ],
    bar_labels=[
        "< Sea Level",
        "0-1,640 Ft",
        "1,640-3,280 Ft",
        "3,280-4,920 Ft",
        "4,920-6,560 Ft",
        "6,560-9,850 Ft",
        "9,850-13,120 Ft",
        ">13,120 Ft",
    ],
    x_label="Elevation",
    y_label="Hours",
    convert_seconds_to_hours=True,
)

V1EUD_EGT = BarChartDef(
    action_id="V1EUD_EGT",
    title="Time at EGT",
    primary_pids=[],
    chart_type="bar",
    source_columns=[
        "EUD_Turbine_in_temp_timer_nvv[0]",
        "EUD_Turbine_in_temp_timer_nvv[1]",
        "EUD_Turbine_in_temp_timer_nvv[2]",
        "EUD_Turbine_in_temp_timer_nvv[3]",
        "EUD_Turbine_in_temp_timer_nvv[4]",
        "EUD_Turbine_in_temp_timer_nvv[5]",
        "EUD_Turbine_in_temp_timer_nvv[6]",
        "EUD_Turbine_in_temp_timer_nvv[7]",
    ],
    bar_labels=[
        "< 32F",
        "0-212F",
        "212-392F",
        "392-752F",
        "752-1112F",
        "1112-1292F",
        "1292-1382F",
        "1382-1562F",
    ],
    x_label="EGT",
    y_label="Hours",
    convert_seconds_to_hours=True,
)


# Registry of all EUD charts by action_id
EUD_CHARTS: dict[str, QuickChartDef] = {
    "V1EUD_SPEED_V_LOAD": V1EUD_SPEED_V_LOAD,
    "V1EUD_SPEED_BAND": V1EUD_SPEED_BAND,
    "V1EUD_ELEVATION": V1EUD_ELEVATION,
    "V1EUD_EGT": V1EUD_EGT,
}
