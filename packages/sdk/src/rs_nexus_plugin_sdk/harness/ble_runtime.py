"""Runtime BLE backend selection for the harness."""

from __future__ import annotations

from dataclasses import dataclass


def normalize_ble_backend(value: str | None) -> str:
    """Normalize public backend labels to internal values."""
    normalized = (value or "bleak").strip().lower()
    if normalized in {"auto", "bleak", "host", "local"}:
        return "bleak"
    if normalized in {"gateway", "nexus_ble_gateway", "ble_gateway"}:
        return "gateway"
    raise ValueError(
        "Unsupported BLE backend value "
        f"{value!r}. Expected one of: auto, bleak, gateway, nexus_ble_gateway."
    )


@dataclass(frozen=True)
class HarnessBLERuntimeConfig:
    """Reduced BLE runtime settings for the plugin harness."""

    backend: str = "bleak"
    gateway_serial_port: str | None = None
    gateway_baudrate: int = 1_000_000
    gateway_protocol_version: int = 1
    gateway_connect_timeout_s: float = 15.0
    gateway_subscribe_timeout_s: float = 5.0
    gateway_write_timeout_s: float = 5.0
    gateway_read_timeout_s: float = 5.0

    @property
    def backend_label(self) -> str:
        if self.backend == "gateway":
            return "nexus_ble_gateway"
        return "bleak"
