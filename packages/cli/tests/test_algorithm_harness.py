from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import sys
from pathlib import Path
import textwrap

CLI_SRC = Path(__file__).resolve().parents[1] / "src"
SDK_SRC = Path(__file__).resolve().parents[2] / "sdk" / "src"
for entry in (CLI_SRC, SDK_SRC):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from nexus_n3_plugin_cli.algorithm_harness.config import AlgorithmHarnessConfig
from nexus_n3_plugin_cli.algorithm_harness import runner as algorithm_runner


@dataclass
class FakeSample:
    timestamp: int
    sensor_type: str
    address: str
    location: str | None
    sampling_rate: int | None
    value: int
    sample_type: str = "mock"


class FakeSensorManager:
    def __init__(self, config, target):
        self.config = config
        self.target = target
        self.listeners = {}
        self.sensors = []

    def register_listener(self, event_name: str, callback) -> None:
        self.listeners[event_name] = callback

    def init_sensor_manager(self, sensors) -> None:
        self.sensors = sensors
        for index, sensor in enumerate(self.sensors, start=1):
            sensor.address = f"sensor-{index}"
            sensor.location = self.config.location or "CHEST"
            sensor.attributes["SAMPLING_RATE"] = 50

    async def dispatch(self, msg: dict):
        message = msg["message"]
        if message == "discover":
            return list(self.sensors)
        if message == "connect_all":
            return list(self.sensors)
        if message == "start_all":
            callback = self.listeners["on_data"]
            for sensor in self.sensors:
                callback(
                    FakeSample(
                        timestamp=1,
                        sensor_type="mock",
                        address=sensor.address,
                        location=sensor.location,
                        sampling_rate=50,
                        value=3,
                    )
                )
                callback(
                    FakeSample(
                        timestamp=2,
                        sensor_type="mock",
                        address=sensor.address,
                        location=sensor.location,
                        sampling_rate=50,
                        value=4,
                    )
                )
            return None
        if message in {"stop_all", "disconnect_all"}:
            return None
        raise AssertionError(f"Unexpected message: {message}")

    def get_connected_sensors(self):
        return list(self.sensors)

    async def identify_all(self):
        return [sensor.address for sensor in self.sensors]

    async def shutdown(self):
        return None


def test_run_algorithm_harness_writes_compute_jsonl(tmp_path: Path, monkeypatch):
    algorithm_root = _create_algorithm_plugin(tmp_path / "algorithm-plugin")
    sensor_root = _create_sensor_plugin(tmp_path / "sensor-plugin")
    monkeypatch.setattr(algorithm_runner, "HarnessSensorManager", FakeSensorManager)

    config = AlgorithmHarnessConfig(
        plugin_root=algorithm_root,
        sensor_plugin_root=sensor_root,
        duration_seconds=0.01,
        sensor_count=1,
        location="CHEST",
    )

    result = asyncio.run(algorithm_runner.run_algorithm_test(config))

    assert result == 0
    capture_dir = algorithm_root / "plugin-test"
    real_time_path = capture_dir / "computed" / "real_time.jsonl"
    intermediate_path = capture_dir / "computed" / "intermediate.jsonl"
    consolidated_path = capture_dir / "computed" / "consolidated.jsonl"
    assert real_time_path.is_file()
    assert intermediate_path.is_file()
    assert consolidated_path.is_file()

    real_time_records = [json.loads(line) for line in real_time_path.read_text(encoding="utf-8").splitlines()]
    intermediate_records = [json.loads(line) for line in intermediate_path.read_text(encoding="utf-8").splitlines()]
    consolidated_records = [json.loads(line) for line in consolidated_path.read_text(encoding="utf-8").splitlines()]

    assert len(real_time_records) == 2
    assert real_time_records[0]["payload"]["algorithm_name"] == "demo_algo"
    assert intermediate_records[0]["payload"]["results"][0]["total"] == 7
    assert consolidated_records[0]["payload"]["results"][0]["grand_total"] == 7


def test_result_stage_normalizes_enum_values():
    from enum import Enum

    class DemoStage(str, Enum):
        REAL_TIME = "real_time"

    payload = type("Payload", (), {"stage": DemoStage.REAL_TIME})()

    assert algorithm_runner._result_stage(payload) == "real_time"


def test_run_algorithm_harness_supports_extracted_bundles(tmp_path: Path, monkeypatch):
    source_root = tmp_path / "source"
    sensor_source_root = _create_sensor_plugin(source_root / "sensor-plugin")
    algorithm_source_root = _create_algorithm_plugin(source_root / "algorithm-plugin")
    bundle_import_root = source_root / "bundle-imports"
    bundle_import_root.mkdir(parents=True, exist_ok=True)
    _copy_package_tree(sensor_source_root / "src" / "demo_sensor", bundle_import_root / "demo_sensor")
    _copy_package_tree(algorithm_source_root / "src" / "demo_algo", bundle_import_root / "demo_algo")

    original_sys_path = list(sys.path)
    sys.path.insert(0, str(bundle_import_root))
    monkeypatch.setattr(algorithm_runner, "HarnessSensorManager", FakeSensorManager)
    try:
        algorithm_bundle_root = _create_algorithm_bundle_root(tmp_path / "algorithm-bundle")
        sensor_bundle_root = _create_sensor_bundle_root(tmp_path / "sensor-bundle")

        config = AlgorithmHarnessConfig(
            plugin_root=algorithm_bundle_root,
            sensor_plugin_root=sensor_bundle_root,
            duration_seconds=0.01,
            sensor_count=1,
            location="CHEST",
        )

        result = asyncio.run(algorithm_runner.run_algorithm_test(config))
    finally:
        sys.path[:] = original_sys_path

    assert result == 0
    capture_dir = algorithm_bundle_root / "plugin-test"
    assert (capture_dir / "computed" / "real_time.jsonl").is_file()
    assert (capture_dir / "computed" / "intermediate.jsonl").is_file()
    assert (capture_dir / "computed" / "consolidated.jsonl").is_file()


def _create_sensor_plugin(plugin_root: Path) -> Path:
    src_dir = plugin_root / "src" / "demo_sensor"
    src_dir.mkdir(parents=True, exist_ok=True)
    (plugin_root / "plugin.json").write_text(
        json.dumps(
            {
                "plugin_id": "demo-sensor",
                "plugin_type": "sensor",
                "display_name": "Demo Sensor",
                "entry_point": "demo_sensor.sensor:DemoSensor",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "sensor.py").write_text(
        textwrap.dedent(
            """
            from nexus_n3_plugin_sdk import SensorBase, SensorType


            class DemoSensor(SensorBase):
                sensor_type = SensorType("DemoSensor", 9000)
                SPEC_PATH = "DemoSensorSpec.yaml"

                def __init__(self, sensor=None):
                    spec = self.load_raw_spec()
                    super().__init__(self.sensor_type, spec)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (src_dir / "DemoSensorSpec.yaml").write_text(
        textwrap.dedent(
            """
            sensor:
              adapter: BLE
            attributes:
              SAMPLING_RATE:
                default: 50
            events:
              - on_data
              - on_error
            locations:
              supported:
                - CHEST
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return plugin_root


def _create_algorithm_plugin(plugin_root: Path) -> Path:
    src_dir = plugin_root / "src" / "demo_algo"
    src_dir.mkdir(parents=True, exist_ok=True)
    (plugin_root / "plugin.json").write_text(
        json.dumps(
            {
                "plugin_id": "demo-algo",
                "plugin_type": "algorithm",
                "display_name": "Demo Algorithm",
                "entry_point": "demo_algo.core:DemoAlgorithm",
                "algorithm_name": "demo_algo",
                "supports_intermediate": True,
                "supports_consolidation": True,
                "executor_entry_points": {
                    "intermediate": "demo_algo.intermediate_executor:DemoIntermediateExecutor",
                    "consolidation": "demo_algo.consolidation_executor:DemoConsolidationExecutor",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "config.yaml").write_text("algorithm:\n  name: demo_algo\n", encoding="utf-8")
    (src_dir / "core.py").write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass

            from nexus_n3_plugin_sdk import AlgorithmBase
            from nexus_n3_plugin_sdk.yaml_loader import load_yaml


            @dataclass
            class DemoResult:
                address: str
                stage: str
                algorithm_name: str
                value: int
                subject_id: str | None = None
                location: str | None = None


            class DemoAlgorithm(AlgorithmBase):
                name = "demo_algo"

                def __init__(self, address, sampling_rate, input_parameters=None):
                    super().__init__(load_yaml(self.yaml_path()))
                    self.address = address
                    self.sampling_rate = sampling_rate
                    self.subject_id = None
                    self.location = None

                def on_sample(self, sample):
                    self.emit_result(
                        DemoResult(
                            address=self.address,
                            stage="real_time",
                            algorithm_name=self.name,
                            value=int(sample.value),
                            subject_id=self.subject_id,
                            location=self.location,
                        )
                    )
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (src_dir / "intermediate_executor.py").write_text(
        textwrap.dedent(
            """
            class DemoIntermediateExecutor:
                def should_run(self, result_buffers):
                    return all(len(items) >= 2 for items in result_buffers.values())

                def run(self, result_buffers):
                    results = []
                    for address, items in result_buffers.items():
                        results.append({"address": address, "total": sum(int(item.value) for item in list(items))})
                    return {
                        "algorithm_name": "demo_algo",
                        "stage": "intermediate_time",
                        "results": results,
                    }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (src_dir / "consolidation_executor.py").write_text(
        textwrap.dedent(
            """
            class DemoConsolidationExecutor:
                def consolidate(self, subject_id, intermediate_records):
                    total = 0
                    for record in intermediate_records:
                        for entry in record.get("results", []):
                            total += int(entry.get("total", 0))
                    return {
                        "algorithm_name": "demo_algo",
                        "stage": "consolidated_time",
                        "results": [{"subject_id": subject_id, "grand_total": total}],
                    }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return plugin_root


def _create_sensor_bundle_root(bundle_root: Path) -> Path:
    bundle_root.mkdir(parents=True, exist_ok=True)
    (bundle_root / "manifest.json").write_text(
        json.dumps(
            {
                "plugin_id": "demo-sensor",
                "plugin_type": "sensor",
                "display_name": "Demo Sensor",
                "entrypoint": {
                    "module": "demo_sensor.sensor",
                    "callable": "DemoSensor",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return bundle_root


def _create_algorithm_bundle_root(bundle_root: Path) -> Path:
    bundle_root.mkdir(parents=True, exist_ok=True)
    (bundle_root / "manifest.json").write_text(
        json.dumps(
            {
                "plugin_id": "demo-algo",
                "plugin_type": "algorithm",
                "display_name": "Demo Algorithm",
                "entrypoint": {
                    "module": "demo_algo.core",
                    "callable": "DemoAlgorithm",
                },
                "capabilities": {
                    "algorithm_name": "demo_algo",
                    "supports_intermediate": True,
                    "supports_consolidation": True,
                    "executor_entry_points": {
                        "intermediate": "demo_algo.intermediate_executor:DemoIntermediateExecutor",
                        "consolidation": "demo_algo.consolidation_executor:DemoConsolidationExecutor",
                    },
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return bundle_root


def _copy_package_tree(source_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for path in source_dir.iterdir():
        if path.is_file():
            target_dir.joinpath(path.name).write_bytes(path.read_bytes())
