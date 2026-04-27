"""Shared type definitions for the plugin SDK."""

from .battery import BatteryStatus
from .connections import ConnectionStatus
from .sensors import AdapterType, SensorType

__all__ = ["AdapterType", "BatteryStatus", "ConnectionStatus", "SensorType"]
