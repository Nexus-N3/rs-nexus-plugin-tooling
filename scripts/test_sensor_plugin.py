#!/usr/bin/env python3
"""Run a source-mode sensor plugin against the reduced harness manager."""

from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import asdict, dataclass, fields, is_dataclass
import json
import sys
from pathlib import Path
from time import time
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
SDK_SRC = REPO_ROOT / "packages" / "sdk" / "src"
CLI_SRC = REPO_ROOT / "packages" / "cli" / "src"

sys.path.insert(0, str(SDK_SRC))
sys.path.insert(0, str(CLI_SRC))


from rs_nexus_plugin_cli.harness_loader import load_plugin_manifest, load_sensor_class, load_sensor_target
from rs_nexus_plugin_sdk.harness import HarnessConfig, HarnessSensorManager


@dataclass(frozen=True)
class _StubSensorType:
    local_name: str


class _CsvCaptureWriter:
    """Write captured harness samples to per-sample-type CSV files."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._writers: dict[str, tuple[object, csv.writer]] = {}
        self.error_log_path = self.output_dir / "errors.log"
        self._error_handle = self.error_log_path.open("w", encoding="utf-8")

    def write_event(self, event_name: str, payload) -> None:
        if event_name == "on_data":
            self._write_sample(payload)
            return
        self._error_handle.write(f"{time():.6f} {event_name} {_serialize_payload(payload)}\n")
        self._error_handle.flush()

    def _write_sample(self, payload) -> None:
        sample_type = str(getattr(payload, "sample_type", type(payload).__name__)).strip().lower()
        file_handle, writer = self._writers.get(sample_type, (None, None))
        if file_handle is None or writer is None:
            path = self.output_dir / f"{sample_type}.csv"
            file_handle = path.open("w", encoding="utf-8", newline="")
            writer = csv.writer(file_handle)
            writer.writerow(self._header_for_payload(payload))
            self._writers[sample_type] = (file_handle, writer)
        writer.writerow(self._row_for_payload(payload))
        file_handle.flush()

    @staticmethod
    def _header_for_payload(payload) -> list[str]:
        if hasattr(payload, "csv_header") and callable(getattr(payload, "csv_header")):
            return [
                "sample_type",
                "sensor_type",
                "address",
                "location",
                "sampling_rate",
            ] + list(payload.csv_header())
        if is_dataclass(payload):
            return [field.name for field in fields(payload)]
        if isinstance(payload, dict):
            return list(payload.keys())
        return ["value"]

    @staticmethod
    def _row_for_payload(payload) -> list[object]:
        if hasattr(payload, "to_csv_row") and callable(getattr(payload, "to_csv_row")):
            return [
                getattr(payload, "sample_type", type(payload).__name__),
                getattr(payload, "sensor_type", None),
                getattr(payload, "address", None),
                getattr(payload, "location", None),
                getattr(payload, "sampling_rate", None),
            ] + list(payload.to_csv_row())
        if is_dataclass(payload):
            return [getattr(payload, field.name) for field in fields(payload)]
        if isinstance(payload, dict):
            return list(payload.values())
        return [payload]

    def close(self) -> None:
        for file_handle, _writer in self._writers.values():
            file_handle.close()
        self._error_handle.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", required=True, type=Path)
    parser.add_argument("--adapter-backend", default="auto")
    parser.add_argument("--sensor-count", type=int, default=1)
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--identify", action="store_true")
    parser.add_argument("--location")
    parser.add_argument("--gateway-serial-port")
    parser.add_argument("--gateway-baudrate", type=int, default=1_000_000)
    parser.add_argument("--gateway-protocol-version", type=int, default=1)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional capture directory. Defaults to plugin-build/harness-captures/<plugin-id>/.",
    )
    parser.add_argument(
        "--attribute",
        action="append",
        default=[],
        help="Override a sensor attribute as KEY=VALUE. VALUE may be JSON.",
    )
    parser.add_argument("--fail-on-no-data", action="store_true")
    return parser.parse_args()


def _parse_attributes(values: list[str]) -> dict[str, object]:
    parsed = {}
    for item in values:
        key, sep, raw_value = item.partition("=")
        if not key or not sep:
            raise ValueError(f"Invalid attribute override: {item!r}")
        try:
            parsed[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            parsed[key] = raw_value
    return parsed


def _build_config(args: argparse.Namespace) -> HarnessConfig:
    return HarnessConfig(
        plugin_root=args.plugin_root.resolve(),
        adapter_backend=args.adapter_backend,
        sensor_count=args.sensor_count,
        duration_seconds=args.duration,
        identify=args.identify,
        fail_on_no_data=args.fail_on_no_data,
        location=args.location,
        gateway_serial_port=args.gateway_serial_port,
        gateway_baudrate=args.gateway_baudrate,
        gateway_protocol_version=args.gateway_protocol_version,
        attributes=_parse_attributes(args.attribute),
    )


def _default_output_dir(plugin_root: Path, plugin_id: str) -> Path:
    safe_plugin_id = plugin_id.replace("/", "_")
    return plugin_root / "plugin-build" / "harness-captures" / safe_plugin_id


def _serialize_payload(value):
    if is_dataclass(value):
        data = asdict(value)
        sample_type = getattr(value, "sample_type", None)
        if sample_type is not None:
            data["sample_type"] = sample_type
        return {key: _serialize_payload(item) for key, item in data.items()}
    if isinstance(value, SimpleNamespace):
        return {key: _serialize_payload(item) for key, item in vars(value).items()}
    if isinstance(value, dict):
        return {str(key): _serialize_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_payload(item) for item in value]
    return value


async def _run() -> int:
    args = _parse_args()
    config = _build_config(args)
    plugin_root = config.plugin_root
    manifest = load_plugin_manifest(plugin_root)
    sensor_cls = load_sensor_class(plugin_root)
    target = load_sensor_target(plugin_root)
    output_dir = (args.output_dir or _default_output_dir(plugin_root, target.plugin_id)).resolve()
    capture_writer = _CsvCaptureWriter(output_dir)

    try:
        manager = HarnessSensorManager(config=config, target=target)
        manager.register_listener("on_data", lambda payload: capture_writer.write_event("on_data", payload))
        manager.register_listener("on_error", lambda payload: capture_writer.write_event("on_error", payload))
        stub = _StubSensorType(local_name=sensor_cls.sensor_type.local_name)
        sensors = [sensor_cls(stub) for _ in range(config.sensor_count)]

        manager.init_sensor_manager(sensors)
        discovered = await manager.dispatch({"message": "discover", "timeout": 5.0})
        if not discovered:
            print("No matching sensors discovered.")
            return 1

        connected = await manager.dispatch({"message": "connect_all"})
        if not connected:
            print("Sensors were discovered but not connected.")
            await manager.shutdown()
            return 1

        try:
            if config.identify:
                for sensor in manager.get_connected_sensors():
                    await manager.dispatch({"message": "identify", "address": sensor.address})
            await manager.dispatch({"message": "start_all"})
            await asyncio.sleep(config.duration_seconds)
            await manager.dispatch({"message": "stop_all"})
            consume_supported = bool(sensors[0].consume_input("harness-source", {"message": "probe"}))
            summary = manager.build_summary(
                entry_point=manifest["entry_point"],
                capabilities=sorted(sensors[0].spec.get("capabilities", [])),
                declared_events=sorted(sensors[0].listeners.keys()),
                consume_input_supported=consume_supported,
            )
        finally:
            await manager.dispatch({"message": "disconnect_all"})
            await manager.shutdown()
    finally:
        capture_writer.close()

    counts = summary.event_counts()
    print(f"Plugin root: {plugin_root}")
    print(f"Plugin id: {summary.plugin_id}")
    print(f"Entry point: {summary.entry_point}")
    print(f"Adapter family: {summary.adapter_family}")
    print(f"Adapter backend: {summary.adapter_backend}")
    print(f"Declared events: {summary.declared_events}")
    print(f"Capabilities: {summary.capabilities}")
    print(f"Observed event counts: {counts}")
    print(f"consume_input accepted probe: {summary.consume_input_supported}")
    print(f"Capture dir: {output_dir}")

    if config.fail_on_no_data and counts.get("on_data", 0) == 0:
        print("Harness run completed without any on_data events.")
        return 2
    return 0


def main() -> int:
    try:
        return asyncio.run(_run())
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
