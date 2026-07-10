"""Focused development harness for sensor plugins."""

from __future__ import annotations

from pathlib import Path

from .harness_runtime import run_sensor_smoke_harness


def run_sensor_harness(plugin_root: Path) -> None:
    """Load a sensor plugin from source and run current smoke checks."""
    result = run_sensor_smoke_harness(plugin_root)
    summary = result["summary"]
    print(f"Plugin root: {result['plugin_root']}")
    print(f"Entry point: {result['entry_point']}")
    print(f"Loaded class: {result['loaded_class']}")
    print(f"Display name: {result['display_name']}")
    print(f"Adapter: {result['adapter']}")
    print(f"Capabilities: {summary.capabilities}")
    print(f"Events: {summary.declared_events}")
    print(f"consume_input accepted probe: {summary.consume_input_supported}")
    print(f"listener emission check: {summary.event_counts().get('on_error', 0)} event(s)")
