"""Local inventory helpers for installed and current plugins."""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import yaml

from .models import AlgorithmOption, CurrentPluginContext, SensorOption


DEFAULT_PLUGIN_ROOT = Path("/opt/nexus-n3-plugins")


def resolve_plugin_root() -> Path:
    env_root = os.environ.get("NEXUS_N3_PLUGIN_ROOT", "").strip()
    return Path(env_root).expanduser().resolve() if env_root else DEFAULT_PLUGIN_ROOT


def load_installed_sensor_options() -> list[SensorOption]:
    options: list[SensorOption] = []
    for catalog in _iter_catalogs():
        if catalog.get("plugin_type") != "sensor" or not catalog.get("enabled", True):
            continue
        install_path = _active_install_path(catalog)
        if install_path is None:
            continue
        manifest = _read_json(install_path / "manifest.json")
        metadata = _load_metadata(install_path, manifest)
        sensor_section = metadata.get("sensor") or {}
        computations = []
        for item in metadata.get("computations", []) or []:
            computations.append(AlgorithmOption(name=str(item), inputs={}))
        options.append(
            SensorOption(
                plugin_id=str(catalog.get("plugin_id") or manifest.get("plugin_id")),
                display_name=str(sensor_section.get("name") or manifest.get("display_name") or catalog.get("display_name")),
                sensor_type=str(sensor_section.get("type") or catalog.get("plugin_id")),
                locations=list(((metadata.get("locations") or {}).get("supported") or [])),
                computations=computations,
                supports_identify=_supports_identify(metadata),
            )
        )
    options.sort(key=lambda item: item.display_name.lower())
    return options


def load_installed_algorithms() -> dict[str, AlgorithmOption]:
    algorithms: dict[str, AlgorithmOption] = {}
    for catalog in _iter_catalogs():
        if catalog.get("plugin_type") != "algorithm" or not catalog.get("enabled", True):
            continue
        install_path = _active_install_path(catalog)
        if install_path is None:
            continue
        manifest = _read_json(install_path / "manifest.json")
        metadata = _load_metadata(install_path, manifest)
        algorithm = metadata.get("algorithm") or {}
        inputs = (((metadata.get("inputs") or {}).get("parameters")) or {}).copy()
        name = str(algorithm.get("name") or manifest.get("capabilities", {}).get("algorithm_name") or catalog.get("plugin_id"))
        algorithms[_normalize(name)] = AlgorithmOption(
            name=name,
            inputs=inputs,
            plugin_id=str(catalog.get("plugin_id") or manifest.get("plugin_id")),
        )
    return algorithms


def detect_current_plugin_context(start_dir: Path) -> CurrentPluginContext | None:
    for candidate in (start_dir, *start_dir.parents):
        plugin_json = candidate / "plugin.json"
        if not plugin_json.is_file():
            continue
        payload = _read_json(plugin_json)
        plugin_type = str(payload.get("plugin_type") or "")
        display_name = str(payload.get("display_name") or payload.get("plugin_id") or candidate.name)
        context = CurrentPluginContext(
            plugin_id=str(payload.get("plugin_id") or candidate.name),
            plugin_type=plugin_type,
            display_name=display_name,
            sensor_type=None,
        )
        if plugin_type == "sensor":
            metadata = _load_repo_sensor_metadata(candidate, payload)
            sensor_type = str(((metadata.get("sensor") or {}).get("type")) or payload.get("plugin_id"))
            return CurrentPluginContext(
                plugin_id=context.plugin_id,
                plugin_type=plugin_type,
                display_name=display_name,
                sensor_type=sensor_type,
            )
        return context
    return None


def load_bundle_summary(bundle_path: Path) -> dict:
    with zipfile.ZipFile(bundle_path, "r") as archive:
        return json.loads(archive.read("manifest.json").decode("utf-8"))


def _iter_catalogs() -> list[dict]:
    plugin_root = resolve_plugin_root()
    catalog_dir = plugin_root / "catalog"
    if not catalog_dir.is_dir():
        return []
    payloads: list[dict] = []
    for path in sorted(catalog_dir.glob("*.json")):
        if path.name in {"plugins.json", "install_failures.json"}:
            continue
        payload = _read_json(path)
        if payload:
            payloads.append(payload)
    return payloads


def _active_install_path(catalog: dict) -> Path | None:
    active_version = catalog.get("active_version")
    version_payload = ((catalog.get("versions") or {}).get(active_version)) or {}
    install_path_raw = version_payload.get("install_path")
    if not install_path_raw:
        return None
    return Path(str(install_path_raw))


def _load_metadata(install_path: Path, manifest: dict) -> dict:
    bundle_dir = install_path / "bundle"
    for candidate in (
        bundle_dir / "metadata" / "sensor_spec.yaml",
        bundle_dir / "metadata" / "algorithm_config.yaml",
    ):
        if candidate.exists():
            return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    spec_path = str(((manifest.get("spec") or {}).get("path")) or "").strip()
    if spec_path:
        for candidate in (bundle_dir / spec_path, bundle_dir / Path(spec_path).name):
            if candidate.exists():
                return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    return {}


def _load_repo_sensor_metadata(plugin_root: Path, plugin_json: dict) -> dict:
    spec_path = str(plugin_json.get("spec_path") or "").strip()
    if not spec_path:
        return {}
    for candidate in (
        plugin_root / spec_path,
        plugin_root / "src" / spec_path,
    ):
        if candidate.exists():
            return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    return {}


def _supports_identify(metadata: dict) -> bool:
    capabilities = {str(item).strip().lower() for item in (metadata.get("capabilities") or []) if item}
    return "identify" in capabilities


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize(value: str) -> str:
    return str(value).strip().lower()
