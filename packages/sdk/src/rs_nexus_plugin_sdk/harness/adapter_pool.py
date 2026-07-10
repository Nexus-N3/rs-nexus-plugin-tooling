"""Reduced adapter pool for the harness sensor manager."""

from __future__ import annotations

from collections import defaultdict

from .adapter_registry import resolve_adapter_class
from .ble_runtime import HarnessBLERuntimeConfig


class HarnessAdapterPool:
    """Owns adapter instances for harness-managed sensors."""

    def __init__(self, ble_runtime_config: HarnessBLERuntimeConfig):
        self.adapters = {}
        self.ble_runtime_config = ble_runtime_config

    def reset(self) -> None:
        self.close_all()
        self.adapters = {}

    def get_or_create(self, adapter_type: str):
        key = str(adapter_type).upper()
        adapter = self.adapters.get(key)
        if adapter is not None:
            return adapter
        adapter_cls = resolve_adapter_class(key, self.ble_runtime_config)
        adapter = adapter_cls(runtime_config=self.ble_runtime_config)
        self.adapters[key] = adapter
        return adapter

    def for_sensor(self, sensor):
        return self.get_or_create(sensor.adapter)

    def group_sensors(self, sensors):
        grouped = defaultdict(list)
        for sensor in sensors:
            grouped[self.for_sensor(sensor)].append(sensor)
        return grouped

    @staticmethod
    def has_method(adapter, method_name: str) -> bool:
        return hasattr(adapter, method_name) and callable(getattr(adapter, method_name))

    def close_all(self) -> None:
        for adapter in list(self.adapters.values()):
            if self.has_method(adapter, "close"):
                try:
                    adapter.close()
                except Exception:
                    pass
