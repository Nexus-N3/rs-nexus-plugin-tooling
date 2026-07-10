"""Harness-facing runtime contracts for source-mode plugin validation."""

from .ble_runtime import HarnessBLERuntimeConfig
from .config import HarnessConfig, HarnessPluginTarget
from .events import HarnessEvent, HarnessSummary
from .sensor_controller import SensorController
from .sensor_manager import HarnessSensorManager, SensorManagerAdapterProtocol

__all__ = [
    "HarnessBLERuntimeConfig",
    "HarnessConfig",
    "HarnessEvent",
    "HarnessPluginTarget",
    "SensorController",
    "HarnessSensorManager",
    "HarnessSummary",
    "SensorManagerAdapterProtocol",
]
