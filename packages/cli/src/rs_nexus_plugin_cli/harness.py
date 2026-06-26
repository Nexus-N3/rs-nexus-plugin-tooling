"""Focused development harness for sensor plugins."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from rs_nexus_plugin_sdk import SensorBase


@dataclass(frozen=True)
class _StubSensorType:
    local_name: str


def _load_plugin_manifest(plugin_root: Path) -> dict:
    manifest_path = plugin_root / "plugin.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Not a plugin source repo: missing plugin.json in {plugin_root}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _load_entry_point_class(entry_point: str):
    module_name, _, attr_name = entry_point.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"Invalid entry point: {entry_point}")
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def run_sensor_harness(plugin_root: Path) -> None:
    """Load a sensor plugin from source and run basic contract checks."""
    plugin_root = plugin_root.resolve()
    manifest = _load_plugin_manifest(plugin_root)
    if manifest.get("plugin_type") != "sensor":
        raise ValueError("Sensor harness only supports sensor plugins")

    src_dir = plugin_root / "src"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Plugin source layout missing src/: {src_dir}")

    sys.path.insert(0, str(src_dir))
    try:
        sensor_cls = _load_entry_point_class(manifest["entry_point"])
    finally:
        sys.path.pop(0)

    if not inspect.isclass(sensor_cls):
        raise TypeError(f"Entry point is not a class: {manifest['entry_point']}")
    if not issubclass(sensor_cls, SensorBase):
        raise TypeError(f"Entry point does not subclass SensorBase: {manifest['entry_point']}")

    stub = _StubSensorType(local_name=sensor_cls.sensor_type.local_name)
    sensor = sensor_cls(stub)
    spec = sensor_cls.load_raw_spec()

    received: list[dict] = []
    sensor.register_listener("on_error", lambda payload: received.append({"event": "on_error", "payload": payload}))
    sensor._emit("on_error", {"message": "harness-check"})
    consume_supported = bool(sensor.consume_input("harness-source", {"message": "probe"}))

    print(f"Plugin root: {plugin_root}")
    print(f"Entry point: {manifest['entry_point']}")
    print(f"Loaded class: {sensor_cls.__module__}.{sensor_cls.__name__}")
    print(f"Display name: {manifest.get('display_name')}")
    print(f"Adapter: {spec.get('sensor', {}).get('adapter')}")
    print(f"Capabilities: {sorted(spec.get('capabilities', []))}")
    print(f"Events: {sorted(sensor.listeners.keys())}")
    print(f"consume_input accepted probe: {consume_supported}")
    print(f"listener emission check: {len(received)} event(s)")
