from domain.snaptypes import SnapType

def handle_header_action(self, action_id: str, snaptype: SnapType):
    print(f"[Quick Chart Button Action] {snaptype}: {action_id}")

    # Dispatch table: map action IDs to handler functions
    dispatch = {
        "V1_BATTERY_TEST": V1_show_battery_chart,
        "V1_RAIL_PRESSURE": V1_show_rail_pressure_chart,
         
        # add more as needed
    }

    # Lookup and call the handler if it exists
    handler = dispatch.get(action_id)
    if handler:
        handler(snaptype)  # or pass whatever args your handlers need
    else:
        print(f"No handler found for action: {action_id}")

def V1_show_battery_chart(snaptype: SnapType):
    print(f"Generating battery chart for {snaptype}")

    

def V1_show_rail_pressure_chart(snaptype: SnapType):
    print(f"Generating rail pressure chart for {snaptype}")