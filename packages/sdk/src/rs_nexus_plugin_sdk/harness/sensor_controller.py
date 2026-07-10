"""Command routing/controller for harness sensor operations."""

from __future__ import annotations

from rs_nexus_plugin_sdk.types.connections import ConnectionStatus


class SensorController:
    """Dispatches sensor-manager commands to harness services."""

    def __init__(
        self,
        sensors_ref,
        get_connected_sensors,
        get_connected_sensor_by_address,
        set_up_sensor,
        register_listeners_with_sensor,
        emit_to_client,
        loop,
        adapter_pool,
        discovery_service,
        connection_service,
        streaming_service,
    ):
        self._sensors_ref = sensors_ref
        self.get_connected_sensors = get_connected_sensors
        self.get_connected_sensor_by_address = get_connected_sensor_by_address
        self.set_up_sensor = set_up_sensor
        self.register_listeners_with_sensor = register_listeners_with_sensor
        self.emit_to_client = emit_to_client
        self.loop = loop
        self.adapter_pool = adapter_pool
        self.discovery_service = discovery_service
        self.connection_service = connection_service
        self.streaming_service = streaming_service
        self.handlers = {
            "discover": (self.handle_discover, "timeout"),
            "connect_all": (self.handle_connect_all, None),
            "discover_and_connect": (self.handle_discover_and_connect, None),
            "disconnect_all": (self.handle_disconnect_all, None),
            "start_all": (self.handle_start_all, None),
            "stop_all": (self.handle_stop_all, None),
            "identify": (self.handle_identify, "address"),
        }

    def _sensors(self):
        return self._sensors_ref()

    async def dispatch(self, msg: dict):
        message_type = msg.get("message")
        handler_entry = self.handlers.get(message_type)
        if handler_entry is None:
            return False
        handler, arg_key = handler_entry
        if arg_key is None:
            return await handler()
        return await handler(msg[arg_key])

    async def handle_discover(self, timeout: float = 5.0):
        print("Sensor controller: discovering sensors", self._sensors())
        return await self.discovery_service.discover_all(
            sensors=self._sensors(),
            loop=self.loop,
            register_listeners_with_sensor=self.register_listeners_with_sensor,
            emit_to_client=self.emit_to_client,
            timeout=timeout,
        )

    async def handle_connect_all(self):
        return await self.connection_service.connect_all(
            sensors=self._sensors(),
            set_up_sensor=self.set_up_sensor,
            emit_to_client=self.emit_to_client,
        )

    async def handle_discover_and_connect(self):
        await self.handle_discover()
        return await self.handle_connect_all()

    async def handle_disconnect_all(self):
        return await self.connection_service.disconnect(
            sensors_to_disconnect=self.get_connected_sensors(),
            emit_to_client=self.emit_to_client,
        )

    async def handle_start_all(self):
        return await self.streaming_service.start(
            sensors=self.get_connected_sensors(),
            emit_to_client=self.emit_to_client,
        )

    async def handle_stop_all(self):
        return await self.streaming_service.stop(
            sensors=self.get_connected_sensors(),
            emit_to_client=self.emit_to_client,
        )

    async def handle_identify(self, address):
        sensors = self.get_connected_sensor_by_address(address)
        if not sensors:
            return []
        sensor = sensors[0]
        identify = getattr(sensor, "identify", None)
        if callable(identify):
            self.emit_to_client("on_identify", sensor.address)
            await identify(self.adapter_pool.for_sensor(sensor))
            return [sensor.address]
        return []
