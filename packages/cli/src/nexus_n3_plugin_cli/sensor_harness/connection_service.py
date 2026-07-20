"""Connection and disconnect service for the harness manager."""

from __future__ import annotations

from nexus_n3_plugin_sdk.types.connections import ConnectionStatus


class ConnectionService:
    """Connect and disconnect flows across adapter groups."""

    def __init__(self, adapter_pool):
        self.adapter_pool = adapter_pool

    async def connect_all(self, sensors, set_up_sensor, emit_to_client):
        connected = []
        adapter_groups = self.adapter_pool.group_sensors(sensors)
        for adapter, sensors_for_adapter in adapter_groups.items():
            for sensor in sensors_for_adapter:
                ok = await adapter.connect_to_device(sensor, adapter)
                if not ok:
                    continue
                if (
                    getattr(sensor, "connection_status", None) is not None
                    and sensor.connection_status.name == ConnectionStatus.CONNECTED.name
                ):
                    await set_up_sensor(sensor)
                    connected.append(sensor)
        emit_to_client("on_connected", connected)
        return connected

    async def disconnect(self, sensors_to_disconnect, emit_to_client):
        disconnected = []
        adapter_groups = self.adapter_pool.group_sensors(sensors_to_disconnect)
        for adapter, sensors_for_adapter in adapter_groups.items():
            for sensor in sensors_for_adapter:
                if await adapter.disconnect(sensor.transport_client):
                    sensor.set_connection_status(ConnectionStatus.DISCONNECTED)
                    disconnected.append(sensor.address)
        emit_to_client("on_disconnected", disconnected)
        return disconnected
