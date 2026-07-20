"""ZeroMQ client for guided nexus-n3-core system tests."""

from __future__ import annotations

import queue
import threading
import time
from typing import Callable

try:
    import zmq
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError("pyzmq is required for nx3-plugin system-test") from exc


class SystemTestClient:
    """Minimal event-driven client for the nexus-n3-core ZeroMQ gateway."""

    def __init__(
        self,
        *,
        cmd_pub_addr: str = "tcp://localhost:5555",
        evt_sub_addr: str = "tcp://localhost:5556",
        event_logger: Callable[[dict], None] | None = None,
    ):
        self.ctx = zmq.Context.instance()
        self.cmd_pub = self.ctx.socket(zmq.PUB)
        self.cmd_pub.setsockopt(zmq.LINGER, 0)
        self.cmd_pub.connect(cmd_pub_addr)

        self.evt_sub = self.ctx.socket(zmq.SUB)
        self.evt_sub.setsockopt(zmq.LINGER, 0)
        self.evt_sub.setsockopt(zmq.RCVTIMEO, 250)
        self.evt_sub.setsockopt_string(zmq.SUBSCRIBE, "")
        self.evt_sub.connect(evt_sub_addr)

        self._event_logger = event_logger
        self._queue: queue.Queue[dict] = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()
        time.sleep(0.2)

    def close(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        try:
            self.evt_sub.close()
        except Exception:
            pass
        try:
            self.cmd_pub.close()
        except Exception:
            pass

    def send_command(self, command: dict) -> None:
        self.cmd_pub.send_json(command)

    def wait_for_event(
        self,
        predicate: Callable[[dict], bool],
        *,
        timeout_s: float,
    ) -> dict:
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for system event.")
            event = self._queue.get(timeout=remaining)
            if predicate(event):
                return event

    def _recv_loop(self) -> None:
        while self._running:
            try:
                event = self.evt_sub.recv_json(flags=0)
            except zmq.Again:
                continue
            except zmq.ZMQError:
                if not self._running:
                    return
                continue
            self._queue.put(event)
            if self._event_logger is not None:
                self._event_logger(event)
