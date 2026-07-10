#!/usr/bin/env python3
"""Run a source-mode sensor plugin against the reduced harness manager."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SDK_SRC = REPO_ROOT / "packages" / "sdk" / "src"
CLI_SRC = REPO_ROOT / "packages" / "cli" / "src"
BLE_TOOLING_SRC = REPO_ROOT.parent / "rs-nexus-ble" / "rs-nexus-ble-tooling"
sys.path.insert(0, str(SDK_SRC))
sys.path.insert(0, str(CLI_SRC))
if BLE_TOOLING_SRC.is_dir():
    sys.path.insert(0, str(BLE_TOOLING_SRC))

from rs_nexus_plugin_cli.harness_loader import load_plugin_manifest, load_sensor_class, load_sensor_target
from rs_nexus_plugin_sdk.harness import HarnessConfig, HarnessSensorManager


@dataclass(frozen=True)
class _StubSensorType:
    local_name: str


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


async def _run() -> int:
    args = _parse_args()
    config = _build_config(args)
    plugin_root = config.plugin_root
    manifest = load_plugin_manifest(plugin_root)
    sensor_cls = load_sensor_class(plugin_root)
    target = load_sensor_target(plugin_root)

    manager = HarnessSensorManager(config=config, target=target)
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
