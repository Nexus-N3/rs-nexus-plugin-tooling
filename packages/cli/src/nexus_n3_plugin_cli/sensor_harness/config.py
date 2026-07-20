"""Shared harness configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class HarnessPluginTarget:
    """Resolved plugin target loaded from a source repository."""

    plugin_root: Path
    plugin_id: str
    plugin_type: str
    display_name: str
    entry_point: str
    adapter_family: str | None = None


@dataclass(frozen=True)
class HarnessConfig:
    """Runtime configuration for source-mode harness execution."""

    plugin_root: Path
    adapter_backend: str = "auto"
    sensor_count: int = 1
    duration_seconds: float = 15.0
    identify: bool = False
    fail_on_no_data: bool = False
    location: str | None = None
    gateway_serial_port: str | None = None
    gateway_baudrate: int = 1_000_000
    gateway_protocol_version: int = 1
    attributes: dict[str, object] = field(default_factory=dict)
