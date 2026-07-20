"""Connection state definitions for sensors."""

from enum import Enum


class ConnectionStatus(Enum):
    """Current connection state for a sensor instance."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
