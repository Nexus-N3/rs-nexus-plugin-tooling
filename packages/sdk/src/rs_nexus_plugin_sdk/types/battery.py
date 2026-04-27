"""Battery status model copied from rs-nexus-os for plugin authoring."""


class BatteryStatus:
    """Battery level and charging state container."""

    def __init__(self, battery_level, is_charging):
        self.battery_level = int(battery_level) if battery_level is not None else None
        self.is_charging = bool(is_charging) if is_charging is not None else None
