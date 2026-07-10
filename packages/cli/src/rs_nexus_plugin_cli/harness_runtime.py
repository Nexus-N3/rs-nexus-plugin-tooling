"""Harness runtime scaffolding built around the SDK sensor-manager facade."""

from __future__ import annotations

from dataclasses import dataclass

from rs_nexus_plugin_sdk.harness import HarnessSensorManager

from .harness_loader import load_plugin_manifest, load_sensor_class, load_sensor_target
from .harness_models import build_harness_config


@dataclass(frozen=True)
class _StubSensorType:
    local_name: str


def run_sensor_smoke_harness(plugin_root, *, adapter_backend: str = "auto") -> dict:
    """Run the current source-tree smoke checks through the new harness shape.

    This keeps today's lightweight validation working while the full
    sensor-manager-backed runtime is brought over from `rs-nexus-os`.
    """
    plugin_root = plugin_root.resolve()
    manifest = load_plugin_manifest(plugin_root)
    sensor_cls = load_sensor_class(plugin_root)
    target = load_sensor_target(plugin_root)
    config = build_harness_config(plugin_root, adapter_backend=adapter_backend)
    manager = HarnessSensorManager(config=config, target=target)

    stub = _StubSensorType(local_name=sensor_cls.sensor_type.local_name)
    sensor = sensor_cls(stub)
    spec = sensor_cls.load_raw_spec()

    sensor.register_listener("on_error", lambda payload: manager.record_event("on_error", payload))
    sensor._emit("on_error", {"message": "harness-check"})
    consume_supported = bool(sensor.consume_input("harness-source", {"message": "probe"}))

    summary = manager.build_summary(
        entry_point=manifest["entry_point"],
        capabilities=sorted(spec.get("capabilities", [])),
        declared_events=sorted(sensor.listeners.keys()),
        consume_input_supported=consume_supported,
    )
    return {
        "plugin_root": str(plugin_root),
        "entry_point": manifest["entry_point"],
        "loaded_class": f"{sensor_cls.__module__}.{sensor_cls.__name__}",
        "display_name": manifest.get("display_name"),
        "adapter": spec.get("sensor", {}).get("adapter"),
        "summary": summary,
    }
