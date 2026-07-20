"""Plugin loading helpers for source-tree and built-bundle harness execution."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path

from nexus_n3_plugin_sdk.sensor_base import SensorBase

from .config import HarnessPluginTarget


def load_plugin_manifest(plugin_root: Path) -> dict:
    """Load and normalize a plugin manifest from source or extracted bundle."""
    plugin_root = plugin_root.resolve()
    source_manifest_path = plugin_root / "plugin.json"
    if source_manifest_path.is_file():
        return json.loads(source_manifest_path.read_text(encoding="utf-8"))

    bundle_manifest_path = plugin_root / "manifest.json"
    if bundle_manifest_path.is_file():
        manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
        entrypoint = manifest.get("entrypoint") or {}
        module_name = entrypoint.get("module")
        callable_name = entrypoint.get("callable")
        if not module_name or not callable_name:
            raise ValueError(f"Invalid bundle manifest entrypoint in {bundle_manifest_path}")
        return {
            "plugin_id": manifest["plugin_id"],
            "plugin_type": manifest["plugin_type"],
            "display_name": manifest.get("display_name"),
            "entry_point": f"{module_name}:{callable_name}",
            "bundle_manifest": manifest,
        }

    raise FileNotFoundError(
        f"Not a plugin source repo or extracted bundle: missing plugin.json/manifest.json in {plugin_root}"
    )


def load_sensor_target(plugin_root: Path) -> HarnessPluginTarget:
    """Build the harness plugin target from the source plugin manifest and spec."""
    plugin_root = plugin_root.resolve()
    manifest = load_plugin_manifest(plugin_root)
    if manifest.get("plugin_type") != "sensor":
        raise ValueError("Sensor harness only supports sensor plugins")

    sensor_cls = _import_sensor_class(_src_dir_or_none(plugin_root), manifest["entry_point"])
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
    return _import_sensor_class(_src_dir_or_none(plugin_root), manifest["entry_point"])


def _src_dir_or_none(plugin_root: Path) -> Path | None:
    src_dir = plugin_root / "src"
    return src_dir if src_dir.is_dir() else None


def _import_sensor_class(src_dir: Path | None, entry_point: str):
    module_name, _, attr_name = entry_point.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"Invalid entry point: {entry_point}")

    if src_dir is not None:
        sys.path.insert(0, str(src_dir))
    try:
        module = importlib.import_module(module_name)
        sensor_cls = getattr(module, attr_name)
    finally:
        if src_dir is not None:
            sys.path.pop(0)

    if not inspect.isclass(sensor_cls):
        raise TypeError(f"Entry point is not a class: {entry_point}")
    if not issubclass(sensor_cls, SensorBase):
        raise TypeError(f"Entry point does not subclass SensorBase: {entry_point}")
    return sensor_cls
