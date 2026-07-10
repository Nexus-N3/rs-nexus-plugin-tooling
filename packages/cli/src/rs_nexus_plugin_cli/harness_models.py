"""CLI-facing harness config helpers."""

from __future__ import annotations

from pathlib import Path

from rs_nexus_plugin_sdk.harness import HarnessConfig


def build_harness_config(
    plugin_root: Path,
    *,
    adapter_backend: str = "auto",
    sensor_count: int = 1,
    duration_seconds: float = 15.0,
    identify: bool = False,
    fail_on_no_data: bool = False,
) -> HarnessConfig:
    """Build one harness config object from CLI arguments."""
    return HarnessConfig(
        plugin_root=plugin_root.resolve(),
        adapter_backend=adapter_backend,
        sensor_count=sensor_count,
        duration_seconds=duration_seconds,
        identify=identify,
        fail_on_no_data=fail_on_no_data,
    )
