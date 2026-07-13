"""Algorithm plugin loading helpers for source-tree and extracted-bundle execution."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path

from rs_nexus_plugin_sdk.algorithm_base import AlgorithmBase

from .config import AlgorithmHarnessTarget


def load_algorithm_manifest(plugin_root: Path) -> dict:
    """Load and normalize an algorithm plugin manifest."""
    plugin_root = plugin_root.resolve()
    source_manifest_path = plugin_root / "plugin.json"
    if source_manifest_path.is_file():
        manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        if manifest.get("plugin_type") != "algorithm":
            raise ValueError(f"Expected an algorithm plugin manifest in {plugin_root}")
        return manifest

    bundle_manifest_path = plugin_root / "manifest.json"
    if bundle_manifest_path.is_file():
        manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
        if manifest.get("plugin_type") != "algorithm":
            raise ValueError(f"Expected an algorithm bundle manifest in {plugin_root}")
        entrypoint = manifest.get("entrypoint") or {}
        capabilities = manifest.get("capabilities") or {}
        executor_entry_points = capabilities.get("executor_entry_points") or {}
        return {
            "plugin_id": manifest["plugin_id"],
            "plugin_type": manifest["plugin_type"],
            "display_name": manifest.get("display_name"),
            "entry_point": "{module}:{callable}".format(**entrypoint),
            "algorithm_name": capabilities.get("algorithm_name") or manifest.get("plugin_id"),
            "supports_intermediate": capabilities.get("supports_intermediate", False),
            "supports_consolidation": capabilities.get("supports_consolidation", False),
            "executor_entry_points": executor_entry_points,
            "bundle_manifest": manifest,
        }

    raise FileNotFoundError(
        f"Not an algorithm plugin source repo or extracted bundle: missing plugin.json/manifest.json in {plugin_root}"
    )


def load_algorithm_target(plugin_root: Path) -> AlgorithmHarnessTarget:
    """Build the harness target from the algorithm plugin manifest."""
    plugin_root = plugin_root.resolve()
    manifest = load_algorithm_manifest(plugin_root)
    return AlgorithmHarnessTarget(
        plugin_root=plugin_root,
        plugin_id=str(manifest["plugin_id"]),
        plugin_type=str(manifest["plugin_type"]),
        display_name=str(manifest.get("display_name") or manifest["plugin_id"]),
        entry_point=str(manifest["entry_point"]),
        algorithm_name=str(manifest.get("algorithm_name") or manifest["plugin_id"]),
        supports_intermediate=bool(manifest.get("supports_intermediate", False)),
        supports_consolidation=bool(manifest.get("supports_consolidation", False)),
        intermediate_entry_point=_executor_entry_point(manifest, "intermediate"),
        consolidation_entry_point=_executor_entry_point(manifest, "consolidation"),
    )


def load_algorithm_class(plugin_root: Path):
    """Load the algorithm class declared by the plugin entry point."""
    manifest = load_algorithm_manifest(plugin_root)
    algorithm_cls = _import_symbol(_src_dir_or_none(plugin_root), str(manifest["entry_point"]))
    if not inspect.isclass(algorithm_cls):
        raise TypeError(f"Algorithm entry point is not a class: {manifest['entry_point']}")
    if not issubclass(algorithm_cls, AlgorithmBase):
        raise TypeError(f"Algorithm entry point does not subclass AlgorithmBase: {manifest['entry_point']}")
    return algorithm_cls


def load_intermediate_executor(plugin_root: Path):
    """Instantiate the intermediate executor if the plugin declares one."""
    manifest = load_algorithm_manifest(plugin_root)
    entry_point = _executor_entry_point(manifest, "intermediate")
    if not entry_point:
        return None
    executor_cls = _import_symbol(_src_dir_or_none(plugin_root), entry_point)
    return executor_cls()


def load_consolidation_executor(plugin_root: Path):
    """Instantiate the consolidation executor if the plugin declares one."""
    manifest = load_algorithm_manifest(plugin_root)
    entry_point = _executor_entry_point(manifest, "consolidation")
    if not entry_point:
        return None
    executor_cls = _import_symbol(_src_dir_or_none(plugin_root), entry_point)
    return executor_cls()


def _executor_entry_point(manifest: dict, stage: str) -> str | None:
    entry_points = manifest.get("executor_entry_points") or {}
    raw = entry_points.get(stage)
    if raw:
        return str(raw)
    return None


def _src_dir_or_none(plugin_root: Path) -> Path | None:
    src_dir = plugin_root / "src"
    return src_dir if src_dir.is_dir() else None


def _import_symbol(src_dir: Path | None, entry_point: str):
    module_name, _, attr_name = entry_point.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"Invalid entry point: {entry_point}")

    if src_dir is not None:
        sys.path.insert(0, str(src_dir))
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)
    finally:
        if src_dir is not None:
            sys.path.pop(0)
