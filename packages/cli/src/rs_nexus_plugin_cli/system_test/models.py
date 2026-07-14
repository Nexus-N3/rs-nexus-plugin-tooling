"""Shared models for guided system testing."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlgorithmOption:
    name: str
    inputs: dict[str, object] = field(default_factory=dict)
    plugin_id: str | None = None


@dataclass(frozen=True)
class SensorOption:
    plugin_id: str
    display_name: str
    sensor_type: str
    locations: list[str]
    computations: list[AlgorithmOption]
    supports_identify: bool = False


@dataclass(frozen=True)
class CurrentPluginContext:
    plugin_id: str
    plugin_type: str
    display_name: str
    sensor_type: str | None = None


@dataclass(frozen=True)
class SubjectPlan:
    subject_ids: list[str]
    sensor_assignments: list["SensorAssignment"]


@dataclass(frozen=True)
class SensorAssignment:
    sensor: SensorOption
    algorithm: AlgorithmOption
    sensor_count: int
    locations: list[str]
