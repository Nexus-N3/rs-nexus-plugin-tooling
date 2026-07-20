from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

CLI_SRC = Path(__file__).resolve().parents[1] / "src"
if str(CLI_SRC) not in sys.path:
    sys.path.insert(0, str(CLI_SRC))

from nexus_n3_plugin_cli.build import build_plugin_bundle


def test_build_sensor_reference_bundle_includes_phase1_files(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[4]
    plugin_root = repo_root / "nexus-n3-plugin-catalog" / "sensors" / "nexus-n3-sensor-movella-dot"

    bundle_path = build_plugin_bundle(
        plugin_root=plugin_root,
        output_dir=tmp_path,
        force=True,
    )

    assert bundle_path.suffix == ".rsnxplugin"
    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "checksums.json" in names
        assert "metadata/sensor_spec.yaml" in names
        assert any(name.startswith("artifacts/nexus_n3_sensor_movella_dot-0.1.0") for name in names)
        assert any(name.startswith("artifacts/nexus_n3_plugin_sdk-0.1.0") for name in names)

        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["plugin_id"] == "movella-dot"
        assert manifest["spec"]["type"] == "sensor_yaml"
        assert manifest["entrypoint"]["module"] == "nexus_n3_sensor_movella_dot.sensor"


def test_build_algorithm_reference_bundle_includes_phase1_files(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[4]
    plugin_root = (
        repo_root
        / "nexus-n3-plugin-catalog"
        / "algorithms"
        / "nexus-n3-algorithm-standard-loading-intensity"
    )

    bundle_path = build_plugin_bundle(
        plugin_root=plugin_root,
        output_dir=tmp_path,
        force=True,
    )

    assert bundle_path.suffix == ".rsnxplugin"
    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "checksums.json" in names
        assert "metadata/algorithm_config.yaml" in names
        assert any(name.startswith("artifacts/nexus_n3_algorithm_standard_loading_intensity-0.1.0") for name in names)
        assert any(name.startswith("artifacts/nexus_n3_plugin_sdk-0.1.0") for name in names)

        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["plugin_id"] == "standard-loading-intensity"
        assert manifest["spec"]["type"] == "algorithm_config"
        assert manifest["capabilities"]["supports_intermediate"] is True
        assert manifest["capabilities"]["supports_consolidation"] is True


def test_build_bundle_includes_extra_artifacts(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[4]
    plugin_root = repo_root / "nexus-n3-plugin-catalog" / "sensors" / "nexus-n3-sensor-movella-dot"
    extra_wheel = tmp_path / "numpy-0.0.0-py3-none-any.whl"
    extra_wheel.write_bytes(b"placeholder wheel content")

    bundle_path = build_plugin_bundle(
        plugin_root=plugin_root,
        output_dir=tmp_path,
        force=True,
        extra_artifacts=[extra_wheel],
    )

    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
        assert f"artifacts/{extra_wheel.name}" in names
