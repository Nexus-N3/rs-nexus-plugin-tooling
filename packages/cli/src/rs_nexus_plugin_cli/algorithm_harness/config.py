"""Shared configuration models for algorithm harness execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AlgorithmHarnessTarget:
    """Resolved algorithm plugin target loaded from a source repository."""

    plugin_root: Path
    plugin_id: str
    plugin_type: str
    display_name: str
    entry_point: str
    algorithm_name: str
    supports_intermediate: bool = False
    supports_consolidation: bool = False
    intermediate_entry_point: str | None = None
    consolidation_entry_point: str | None = None


@dataclass(frozen=True)
class AlgorithmHarnessConfig:
    """Runtime configuration for source-mode algorithm harness execution."""

    plugin_root: Path
    sensor_plugin_root: Path
    adapter_backend: str = "auto"
    sensor_count: int = 1
    duration_seconds: float = 15.0
    identify: bool = False
    fail_on_no_results: bool = False
    location: str | None = None
    gateway_serial_port: str | None = None
    gateway_baudrate: int = 1_000_000
    gateway_protocol_version: int = 1
    sensor_attributes: dict[str, object] = field(default_factory=dict)
    algorithm_input_parameters: dict[str, object] = field(default_factory=dict)
    subject_id: str = "harness-subject-1"
