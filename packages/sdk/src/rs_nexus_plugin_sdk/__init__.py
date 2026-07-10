"""Shared SDK contracts for RS Nexus plugins."""

from .algorithm_base import AlgorithmBase
from .executor_base import (
    ExecutorBase,
    build_consolidated_result,
    build_intermediate_result,
)
from .harness import (
    HarnessBLERuntimeConfig,
    HarnessConfig,
    HarnessEvent,
    HarnessPluginTarget,
    SensorController,
    HarnessSensorManager,
    HarnessSummary,
    SensorManagerAdapterProtocol,
)
from .sensor_base import SensorBase
from .types.battery import BatteryStatus
from .types.sensors import SensorType

__all__ = [
    "AlgorithmBase",
    "BatteryStatus",
    "ExecutorBase",
    "HarnessBLERuntimeConfig",
    "HarnessConfig",
    "HarnessEvent",
    "HarnessPluginTarget",
    "SensorController",
    "HarnessSensorManager",
    "HarnessSummary",
    "SensorManagerAdapterProtocol",
    "SensorBase",
    "SensorType",
    "build_consolidated_result",
    "build_intermediate_result",
]
