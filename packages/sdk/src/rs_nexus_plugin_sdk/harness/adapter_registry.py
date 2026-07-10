"""Adapter selection for the reduced harness runtime."""

from __future__ import annotations

from .adapters.ble_adapter import BLEAdapter
from .adapters.gateway_ble_adapter import GatewayBLEAdapter
from .ble_runtime import HarnessBLERuntimeConfig


def resolve_adapter_class(
    adapter_type: str,
    ble_runtime_config: HarnessBLERuntimeConfig,
):
    """Resolve the adapter class for a sensor adapter family."""
    key = str(adapter_type).upper()
    if key != "BLE":
        raise ValueError(f"Unsupported harness adapter type: {key}")
    if ble_runtime_config.backend == "bleak":
        return BLEAdapter
    if ble_runtime_config.backend == "gateway":
        return GatewayBLEAdapter
    raise ValueError(f"Unsupported harness BLE backend: {ble_runtime_config.backend}")
