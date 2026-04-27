"""Sensor type and adapter enumerations copied from rs-nexus-os."""

from enum import Enum
from typing import NamedTuple


class SensorType(NamedTuple):
    """Sensor identity information used by plugin implementations."""

    local_name: str
    manufacturer_id: int


class AdapterType(Enum):
    """Supported adapter types."""

    BLE = "BLE"
    SERIAL = "Serial"
    WIFI = "WiFi"
