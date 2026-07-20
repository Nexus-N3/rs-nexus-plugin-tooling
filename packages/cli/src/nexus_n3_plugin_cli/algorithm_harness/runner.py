"""Source-mode algorithm harness runner."""

from __future__ import annotations

import argparse
import asyncio
from enum import Enum
import json
from pathlib import Path
from time import time
from types import SimpleNamespace

from nexus_n3_plugin_cli.sensor_harness.config import HarnessConfig
from nexus_n3_plugin_cli.sensor_harness.plugin_loader import (
    load_plugin_manifest as load_sensor_manifest,
    load_sensor_class,
    load_sensor_target,
)
from nexus_n3_plugin_cli.sensor_harness.runner import CsvCaptureWriter, parse_attributes, serialize_payload
from nexus_n3_plugin_cli.sensor_harness.sensor_manager import HarnessSensorManager

from .compute_runtime import HarnessComputeManager
from .config import AlgorithmHarnessConfig
from .plugin_loader import (
    load_algorithm_class,
    load_algorithm_manifest,
    load_algorithm_target,
    load_consolidation_executor,
    load_intermediate_executor,
)


class JsonlCaptureWriter:
    """Write compute events to JSONL files grouped by stage."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._handles = {
            "real_time": (self.output_dir / "real_time.jsonl").open("w", encoding="utf-8"),
            "intermediate_time": (self.output_dir / "intermediate.jsonl").open("w", encoding="utf-8"),
            "consolidated_time": (self.output_dir / "consolidated.jsonl").open("w", encoding="utf-8"),
        }

    def write(self, stage: str, payload) -> None:
        normalized_stage = str(stage).strip().lower()
        handle = self._handles.get(normalized_stage)
        if handle is None:
            return
        record = {
            "timestamp": time(),
            "stage": normalized_stage,
            "payload": serialize_payload(payload),
        }
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()

    def close(self) -> None:
        for handle in self._handles.values():
            handle.close()


def build_harness_config(args: argparse.Namespace) -> AlgorithmHarnessConfig:
    """Build an AlgorithmHarnessConfig from parsed CLI args."""
    return AlgorithmHarnessConfig(
        plugin_root=args.plugin_root.resolve(),
        sensor_plugin_root=args.sensor_plugin_root.resolve(),
        adapter_backend=args.adapter_backend,
        sensor_count=args.sensor_count,
        duration_seconds=args.duration,
        identify=args.identify,
        fail_on_no_results=args.fail_on_no_results,
        location=args.location,
        gateway_serial_port=args.gateway_serial_port,
        gateway_baudrate=args.gateway_baudrate,
        gateway_protocol_version=args.gateway_protocol_version,
        sensor_attributes=parse_attributes(args.attribute),
        algorithm_input_parameters=parse_attributes(args.algorithm_input),
        subject_id=args.subject_id,
    )


def default_output_dir(plugin_root: Path) -> Path:
    """Return the default output directory for an algorithm harness run."""
    return plugin_root / "plugin-test"


def _sensor_harness_config(config: AlgorithmHarnessConfig) -> HarnessConfig:
    return HarnessConfig(
        plugin_root=config.sensor_plugin_root,
        adapter_backend=config.adapter_backend,
        sensor_count=config.sensor_count,
        duration_seconds=config.duration_seconds,
        identify=config.identify,
        fail_on_no_data=False,
        location=config.location,
        gateway_serial_port=config.gateway_serial_port,
        gateway_baudrate=config.gateway_baudrate,
        gateway_protocol_version=config.gateway_protocol_version,
        attributes=config.sensor_attributes,
    )


def _result_stage(result) -> str:
    if isinstance(result, dict):
        return str(result.get("stage", "unknown"))
    stage = getattr(result, "stage", "unknown")
    if isinstance(stage, Enum):
        return str(stage.value)
    return str(stage)


def _result_summary(result) -> str:
    payload = serialize_payload(result)
    if isinstance(payload, dict):
        algorithm_name = payload.get("algorithm_name")
        stage = payload.get("stage")
        address = payload.get("address")
        location = payload.get("location")
        keys = sorted(payload.keys())
        return (
            f"algorithm={algorithm_name} stage={stage} address={address} "
            f"location={location} keys={keys}"
        )
    return str(payload)


def _consolidation_records(results: list[dict], algorithm_name: str) -> list[dict]:
    return [
        item
        for item in results
        if str(item.get("algorithm_name", "")).strip().lower() == algorithm_name.strip().lower()
    ]


async def run_algorithm_test(config: AlgorithmHarnessConfig, *, output_dir: Path | None = None) -> int:
    """Execute the algorithm harness against a sensor source plugin and algorithm source plugin."""
    algorithm_manifest = load_algorithm_manifest(config.plugin_root)
    algorithm_target = load_algorithm_target(config.plugin_root)
    algorithm_cls = load_algorithm_class(config.plugin_root)
    intermediate_executor = load_intermediate_executor(config.plugin_root)
    consolidation_executor = load_consolidation_executor(config.plugin_root)

    sensor_manifest = load_sensor_manifest(config.sensor_plugin_root)
    sensor_cls = load_sensor_class(config.sensor_plugin_root)
    sensor_target = load_sensor_target(config.sensor_plugin_root)

    capture_dir = (output_dir or default_output_dir(config.plugin_root)).resolve()
    sensor_capture_writer = CsvCaptureWriter(capture_dir / "sensor-data")
    compute_capture_writer = JsonlCaptureWriter(capture_dir / "computed")
    sensor_manager = HarnessSensorManager(config=_sensor_harness_config(config), target=sensor_target)
    compute_manager = HarnessComputeManager(
        error_cb=lambda message: sensor_capture_writer.write_event("on_error", {"error": message})
    )
    intermediate_results: list[dict] = []

    def on_sensor_data(payload) -> None:
        sensor_capture_writer.write_event("on_data", payload)
        compute_manager.ingest_sample(payload)

    def on_compute_result(result) -> None:
        stage = _result_stage(result)
        compute_capture_writer.write(stage, result)
        print(f"[compute:{stage}] {_result_summary(result)}")

    def on_intermediate_result(result) -> None:
        stage = _result_stage(result)
        payload = serialize_payload(result)
        if isinstance(payload, dict):
            intermediate_results.append(payload)
        compute_capture_writer.write(stage, result)
        print(f"[compute:{stage}] {_result_summary(result)}")

    try:
        sensor_manager.register_listener("on_data", on_sensor_data)
        sensor_manager.register_listener("on_error", lambda payload: sensor_capture_writer.write_event("on_error", payload))
        compute_manager.register_result_listener(on_compute_result)
        compute_manager.register_intermediate_result_listener(on_intermediate_result)

        if intermediate_executor is not None:
            compute_manager.register_intermediate_executor(
                algorithm_target.algorithm_name,
                intermediate_executor,
            )
        if consolidation_executor is not None:
            compute_manager.register_consolidation_executor(
                algorithm_target.algorithm_name,
                consolidation_executor,
            )

        stub = SimpleNamespace(local_name=sensor_cls.sensor_type.local_name)
        sensors = [sensor_cls(stub) for _ in range(config.sensor_count)]
        sensor_manager.init_sensor_manager(sensors)

        discovered = await sensor_manager.dispatch({"message": "discover", "timeout": 5.0})
        if not discovered:
            print("No matching sensors discovered.")
            return 1

        connected = await sensor_manager.dispatch({"message": "connect_all"})
        if not connected:
            print("Sensors were discovered but not connected.")
            await sensor_manager.shutdown()
            return 1

        connected_sensors = sensor_manager.get_connected_sensors()
        for sensor in connected_sensors:
            algorithm = algorithm_cls(
                address=sensor.address,
                sampling_rate=sensor.attributes.get("SAMPLING_RATE"),
                input_parameters=config.algorithm_input_parameters or None,
            )
            algorithm.subject_id = config.subject_id
            algorithm.location = sensor.location
            if hasattr(algorithm, "register_result_listener"):
                algorithm.register_result_listener(compute_manager.on_algorithm_result)
            else:
                algorithm.result_callback = compute_manager.on_algorithm_result
            if hasattr(algorithm, "register_compute_delegate"):
                algorithm.register_compute_delegate(lambda *_args, **_kwargs: False)
            else:
                algorithm.compute_delegate = lambda *_args, **_kwargs: False
            compute_manager.register_algorithm(sensor.address, algorithm)

        try:
            if config.identify:
                await sensor_manager.identify_all()
            await sensor_manager.dispatch({"message": "start_all"})
            await asyncio.sleep(config.duration_seconds)
            await sensor_manager.dispatch({"message": "stop_all"})
            compute_manager.wait_until_idle(timeout=max(5.0, config.duration_seconds))
        finally:
            await sensor_manager.dispatch({"message": "disconnect_all"})
            await sensor_manager.shutdown()

        consolidated = compute_manager.run_consolidation_for_subject(
            config.subject_id,
            algorithm_target.algorithm_name,
            _consolidation_records(intermediate_results, algorithm_target.algorithm_name),
        )
        if consolidated is not None:
            stage = _result_stage(consolidated)
            compute_capture_writer.write(stage, consolidated)
            print(f"[compute:{stage}] {_result_summary(consolidated)}")
    finally:
        compute_manager.shutdown()
        sensor_capture_writer.close()
        compute_capture_writer.close()

    result_count = len(compute_manager.get_results(algorithm_target.algorithm_name))
    print(f"Algorithm plugin root: {config.plugin_root}")
    print(f"Sensor plugin root: {config.sensor_plugin_root}")
    print(f"Algorithm id: {algorithm_target.plugin_id}")
    print(f"Algorithm name: {algorithm_target.algorithm_name}")
    print(f"Sensor id: {sensor_manifest['plugin_id']}")
    print(f"Sensor entry point: {sensor_manifest['entry_point']}")
    print(f"Algorithm entry point: {algorithm_manifest['entry_point']}")
    print(f"Observed compute results: {result_count}")
    print(f"Capture dir: {capture_dir}")

    if config.fail_on_no_results and result_count == 0:
        print("Harness run completed without any compute results.")
        return 2
    return 0
