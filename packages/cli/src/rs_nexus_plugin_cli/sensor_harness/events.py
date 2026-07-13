"""Shared event and summary models for the harness runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HarnessEvent:
    """One event observed from the plugin runtime."""

    event_name: str
    payload: Any
    payload_type: str
    timestamp: float


@dataclass
class HarnessSummary:
    """Aggregate summary emitted by the harness after a run."""

    plugin_id: str
    entry_point: str
    adapter_family: str | None
    adapter_backend: str
    capabilities: list[str]
    declared_events: list[str]
    observed_events: list[HarnessEvent] = field(default_factory=list)
    consume_input_supported: bool = False

    def event_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.observed_events:
            counts[item.event_name] = counts.get(item.event_name, 0) + 1
        return counts
