"""Source-tree loading helpers for SDK-side sensor harness execution."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path

from rs_nexus_plugin_sdk import SensorBase

from .config import HarnessPluginTarget


def load_plugin_manifest(plugin_root: Path) -> dict:
    """Load and minimally validate a plugin manifest from a source tree."""
    manifest_path = plugin_root / "plugin.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Not a plugin source repo: missing plugin.json in {plugin_root}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_sensor_target(plugin_root: Path) -> HarnessPluginTarget:
    """Build the harness plugin target from the source plugin manifest and spec."""
    plugin_root = plugin_root.resolve()
    manifest = load_plugin_manifest(plugin_root)
    if manifest.get("plugin_type") != "sensor":
        raise ValueError("Sensor harness only supports sensor plugins")

    src_dir = plugin_root / "src"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Plugin source layout missing src/: {src_dir}")

    sensor_cls = _import_sensor_class(src_dir, manifest["entry_point"])
    spec = sensor_cls.load_raw_spec()
    return HarnessPluginTarget(
        plugin_root=plugin_root,
        plugin_id=manifest["plugin_id"],
        plugin_type=manifest["plugin_type"],
        display_name=manifest.get("display_name") or sensor_cls.sensor_type.local_name,
        entry_point=manifest["entry_point"],
        adapter_family=spec.get("sensor", {}).get("adapter"),
    )


def load_sensor_class(plugin_root: Path):
    """Load the sensor class declared by the plugin entry point."""
    manifest = load_plugin_manifest(plugin_root)
    src_dir = plugin_root / "src"
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Plugin source layout missing src/: {src_dir}")
    return _import_sensor_class(src_dir, manifest["entry_point"])


def _import_sensor_class(src_dir: Path, entry_point: str):
    module_name, _, attr_name = entry_point.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"Invalid entry point: {entry_point}")

    sys.path.insert(0, str(src_dir))
    try:
        module = importlib.import_module(module_name)
        sensor_cls = getattr(module, attr_name)
    finally:
        sys.path.pop(0)

    if not inspect.isclass(sensor_cls):
        raise TypeError(f"Entry point is not a class: {entry_point}")
    if not issubclass(sensor_cls, SensorBase):
        raise TypeError(f"Entry point does not subclass SensorBase: {entry_point}")
    return sensor_cls
