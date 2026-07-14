"""Guided interactive rs-nexus-os system test workflow."""

from __future__ import annotations

import time
from pathlib import Path

from .client import SystemTestClient
from .inventory import detect_current_plugin_context, load_installed_algorithms, load_installed_sensor_options
from .models import AlgorithmOption, SensorAssignment, SensorOption, SubjectPlan
from . import protocol as mt
from .wizard import WizardCancelled, prompt_bool, prompt_choice, prompt_int, prompt_text


def run_system_test(*, start_dir: Path) -> int:
    """Run the interactive sensor + algorithm system test flow."""
    current_plugin = detect_current_plugin_context(start_dir)
    client = SystemTestClient()
    client.start()
    try:
        server_ready = _check_server_ready(client)
        server_capabilities = server_ready.get("payload", {})
        live_sensor_names = {
            _normalize(item.get("name"))
            for item in (server_capabilities.get("supported_sensors") or [])
            if isinstance(item, dict)
        }
        live_algorithms = {
            _normalize(name)
            for name in (server_capabilities.get("supported_algorithms") or [])
            if name
        }
        sensors = _resolve_available_sensors(live_sensor_names)
        if current_plugin and current_plugin.plugin_type == "sensor":
            if current_plugin.sensor_type and _normalize(current_plugin.sensor_type) not in live_sensor_names:
                print("")
                print(f"Current sensor plugin '{current_plugin.display_name}' is not visible to the running rs-nexus-os.")
                print("Install its bundle first with `nx3-plugin install --bundle-path ...`, then rerun `nx3-plugin system-test`.")
                return 1
        if not sensors:
            print("No installed sensor plugins are visible to the running rs-nexus-os.")
            return 1

        subject_plan = _prompt_for_subject_plan(sensors, live_algorithms, current_plugin)
        identify_enabled = any(item.sensor.supports_identify for item in subject_plan.sensor_assignments) and prompt_bool(
            "Run identify prompts after connect?",
            default=False,
        )

        subject_payload = _build_subject_payload(subject_plan=subject_plan)
        subject_ids = [entry["subject_id"] for entry in subject_payload]

        print("")
        print("Initializing system test")
        client.send_command(
            {
                "type": mt.CMD_INIT_SYSTEM,
                "payload": {
                    "subjects": subject_payload,
                    "init_label": "nx3_plugin_system_test",
                },
            }
        )
        _wait_for_success(client, mt.EVT_SYSTEM_INITIALIZED, timeout_s=15.0)

        print("Discovering sensors")
        client.send_command(
            {
                "type": mt.CMD_DISCOVER_SENSORS_FOR_SUBJECTS,
                "payload": {"subject_ids": subject_ids},
            }
        )
        _wait_for_success(client, mt.EVT_SENSORS_DISCOVERED, timeout_s=30.0)

        print("Connecting sensors")
        client.send_command(
            {
                "type": mt.CMD_CONNECT_SUBJECTS,
                "payload": {"subject_ids": subject_ids},
            }
        )
        _wait_for_success(client, mt.EVT_SENSOR_CONNECTED, timeout_s=30.0)

        if identify_enabled:
            for subject_id in subject_ids:
                for assignment in subject_plan.sensor_assignments:
                    if not assignment.sensor.supports_identify:
                        continue
                    for location in assignment.locations:
                        response = prompt_text(
                            f"Press Enter to identify {subject_id} {assignment.sensor.display_name} at {location}, or type skip to continue. "
                        ).strip().lower()
                        if response == "skip":
                            continue
                        client.send_command(
                            {
                                "type": mt.CMD_IDENTIFY_SENSOR,
                                "payload": {"subject_id": subject_id, "location": location},
                            }
                        )
                        try:
                            _wait_for_success(client, mt.EVT_SENSOR_IDENTIFIED, timeout_s=10.0)
                        except TimeoutError:
                            print("Identify event timed out; continuing.")

        print("")
        print("System test setup complete.")
        print(f"  subjects: {', '.join(subject_plan.subject_ids)}")
        for assignment in subject_plan.sensor_assignments:
            print(
                "  sensor_assignment: "
                f"{assignment.sensor.display_name} x{assignment.sensor_count} "
                f"algorithm={assignment.algorithm.name} "
                f"locations={', '.join(assignment.locations)}"
            )
        prompt_text("Press Enter to start streaming. ")
        client.send_command(
            {
                "type": mt.CMD_START_STREAM_FOR_SUBJECTS,
                "payload": {
                    "subject_ids": subject_ids,
                    "tag": "system_test",
                    "session_timestamp": time.strftime("%Y%m%d_%H%M%S"),
                },
            }
        )
        _wait_for_stream_start(client)

        prompt_text("Official streaming active. Press Enter to stop. ")
        stop_session_id = f"system-test-stop-{int(time.time())}"
        client.send_command(
            {
                "type": mt.CMD_STOP_STREAM_FOR_SUBJECTS,
                "payload": {
                    "subject_ids": subject_ids,
                    "stop_session_id": stop_session_id,
                },
            }
        )
        drained = _wait_for_success(client, mt.EVT_STREAM_DRAINED, timeout_s=60.0)

        prompt_text("Press Enter to disconnect sensors. ")
        client.send_command(
            {
                "type": mt.CMD_DISCONNECT_SUBJECTS,
                "payload": {"subject_ids": subject_ids},
            }
        )
        try:
            disconnected = _wait_for_success(client, mt.EVT_SENSOR_DISCONNECTED, timeout_s=15.0)
            disconnected_sensors = (disconnected.get("payload") or {}).get("disconnected_sensors") or []
            print(f"Disconnected sensors: {len(disconnected_sensors)}")
        except TimeoutError:
            print("Disconnect confirmation timed out; the disconnect command was sent.")

        payload = drained.get("payload", {})
        print("")
        print("System test complete.")
        print(f"  subjects: {', '.join(subject_plan.subject_ids)}")
        for assignment in subject_plan.sensor_assignments:
            print(
                "  sensor_assignment: "
                f"{assignment.sensor.display_name} x{assignment.sensor_count} "
                f"algorithm={assignment.algorithm.name} "
                f"locations={', '.join(assignment.locations)}"
            )
        print(f"  session_dir: {payload.get('session_dir')}")
        if payload.get("session_archive_path"):
            print(f"  session_archive_path: {payload.get('session_archive_path')}")
        print(f"  status: {payload.get('status')}")
        return 0
    except WizardCancelled as exc:
        print(str(exc))
        return 1
    finally:
        client.close()


def _check_server_ready(client: SystemTestClient) -> dict:
    print("Checking rs-nexus-os readiness...")
    deadline = time.monotonic() + 10.0
    last_error: TimeoutError | None = None
    while time.monotonic() < deadline:
        client.send_command({"type": mt.CMD_IS_SERVER_READY, "payload": {}})
        try:
            event = client.wait_for_event(
                lambda item: item.get("type") == mt.EVT_SERVER_READY,
                timeout_s=min(2.0, max(deadline - time.monotonic(), 0.1)),
            )
            payload = event.get("payload", {})
            if payload.get("msg") != "System Server Ready":
                raise RuntimeError("rs-nexus-os responded but is not ready for system testing.")
            print("rs-nexus-os is ready.")
            return event
        except TimeoutError as exc:
            last_error = exc
            continue
    raise RuntimeError(
        "Timed out waiting for rs-nexus-os readiness on the standard ZeroMQ gateway. "
        "Confirm rs-nexus-os is running and the zeromq gateway is active."
    ) from last_error


def _resolve_available_sensors(live_sensor_names: set[str]) -> list[SensorOption]:
    sensors = []
    for sensor in load_installed_sensor_options():
        if _normalize(sensor.sensor_type) in live_sensor_names:
            sensors.append(sensor)
    return sensors


def _prompt_for_subject_plan(
    sensors: list[SensorOption],
    live_algorithms: set[str],
    current_plugin,
) -> SubjectPlan:
    subject_count = prompt_int("How many subjects should be used (1-4)? ", minimum=1, maximum=4)
    sensor_assignments = _prompt_for_sensor_assignments(sensors, live_algorithms, current_plugin)
    subject_ids = [f"subject{index}" for index in range(1, subject_count + 1)]
    return SubjectPlan(subject_ids=subject_ids, sensor_assignments=sensor_assignments)


def _prompt_for_sensor_assignments(
    sensors: list[SensorOption],
    live_algorithms: set[str],
    current_plugin,
) -> list[SensorAssignment]:
    assignments: list[SensorAssignment] = []
    used_plugin_ids: set[str] = set()
    used_locations: set[str] = set()
    total_sensor_count = 0
    while True:
        available_sensors = [sensor for sensor in sensors if sensor.plugin_id not in used_plugin_ids]
        if not available_sensors:
            break
        sensor = _prompt_for_sensor(available_sensors, current_plugin if not assignments else None)
        algorithm = _prompt_for_algorithm(sensor, live_algorithms, current_plugin if not assignments else None)
        max_sensor_count = min(len(sensor.locations), 8 - total_sensor_count)
        if max_sensor_count <= 0:
            raise RuntimeError("The selected sensor set exceeds the maximum allowed sensors per subject.")
        sensor_count = prompt_int(
            f"How many {sensor.display_name} sensors per subject (1-{max_sensor_count})? ",
            minimum=1,
            maximum=max_sensor_count,
        )
        locations = _prompt_for_locations(sensor, sensor_count, used_locations)
        assignments.append(
            SensorAssignment(
                sensor=sensor,
                algorithm=algorithm,
                sensor_count=sensor_count,
                locations=locations,
            )
        )
        used_plugin_ids.add(sensor.plugin_id)
        used_locations.update(locations)
        total_sensor_count += sensor_count
        if total_sensor_count >= 8:
            break
        if not prompt_bool("Add another sensor family to this test?", default=False):
            break
    return assignments


def _prompt_for_sensor(sensors: list[SensorOption], current_plugin) -> SensorOption:
    if current_plugin and current_plugin.plugin_type == "sensor":
        for sensor in sensors:
            if sensor.plugin_id == current_plugin.plugin_id:
                print(f"Testing current sensor plugin: {sensor.display_name}")
                return sensor
    options = [
        f"{sensor.display_name} [{sensor.sensor_type}] locations={', '.join(sensor.locations) or 'none'}"
        for sensor in sensors
    ]
    selected = prompt_choice("Choose the sensor plugin to test: ", options)
    return sensors[selected]


def _prompt_for_locations(sensor: SensorOption, sensor_count: int, used_locations: set[str]) -> list[str]:
    selected_locations: list[str] = []
    for index in range(sensor_count):
        remaining = [
            item for item in sensor.locations
            if item not in selected_locations and item not in used_locations
        ]
        if not remaining:
            raise RuntimeError(
                f"Sensor '{sensor.display_name}' does not have enough unique remaining locations for this subject."
            )
        choice = prompt_choice(
            f"Choose location {index + 1} for {sensor.display_name}: ",
            remaining,
        )
        selected_locations.append(remaining[choice])
    return selected_locations


def _build_subject_payload(*, subject_plan: SubjectPlan) -> list[dict]:
    sensors_payload = [
        {
            "local_name": assignment.sensor.display_name,
            "number_of": assignment.sensor_count,
            "compute_algorithm": {
                "name": assignment.algorithm.name,
                "inputs": assignment.algorithm.inputs,
            },
            "locations": list(assignment.locations),
        }
        for assignment in subject_plan.sensor_assignments
    ]
    return [
        {
            "subject_id": subject_id,
            "sensors": [
                {
                    "local_name": item["local_name"],
                    "number_of": item["number_of"],
                    "compute_algorithm": {
                        "name": item["compute_algorithm"]["name"],
                        "inputs": dict(item["compute_algorithm"]["inputs"]),
                    },
                    "locations": list(item["locations"]),
                }
                for item in sensors_payload
            ],
        }
        for subject_id in subject_plan.subject_ids
    ]

def _prompt_for_algorithm(
    sensor: SensorOption,
    live_algorithms: set[str],
    current_plugin,
) -> AlgorithmOption:
    installed_algorithms = load_installed_algorithms()
    if current_plugin and current_plugin.plugin_type == "algorithm":
        if _normalize(current_plugin.display_name) not in live_algorithms and _normalize(current_plugin.plugin_id) not in {
            option.plugin_id or ""
            for option in installed_algorithms.values()
        }:
            print("")
            print(f"Current algorithm plugin '{current_plugin.display_name}' is not visible to the running rs-nexus-os.")
            print("Install its bundle first with `nx3-plugin install --bundle-path ...`, then rerun `nx3-plugin system-test`.")
            raise RuntimeError("Current algorithm plugin is not installed.")
    candidates: list[AlgorithmOption] = []
    for computation in sensor.computations:
        if _normalize(computation.name) not in live_algorithms:
            continue
        installed = installed_algorithms.get(_normalize(computation.name))
        if installed is None:
            continue
        candidates.append(
            AlgorithmOption(
                name=installed.name,
                inputs=installed.inputs or computation.inputs,
                plugin_id=installed.plugin_id,
            )
        )
    pass_through = installed_algorithms.get("pass_through")
    if pass_through is not None and "pass_through" in live_algorithms:
        if not any(_normalize(item.name) == "pass_through" for item in candidates):
            candidates.append(pass_through)
    if not candidates:
        raise RuntimeError(
            f"Sensor '{sensor.display_name}' has no compatible installed algorithm visible to the running rs-nexus-os. "
            "Install a compatible algorithm bundle first, or install pass_through for raw-data-oriented testing."
        )
    if current_plugin and current_plugin.plugin_type == "algorithm":
        for candidate in candidates:
            if candidate.plugin_id == current_plugin.plugin_id or _normalize(candidate.name) == _normalize(current_plugin.display_name):
                print(f"Using current algorithm plugin: {candidate.name}")
                return candidate
    options = [
        f"{item.name}" + (f" inputs={sorted(item.inputs.keys())}" if item.inputs else "")
        for item in candidates
    ]
    selected = prompt_choice("Choose the algorithm to use: ", options)
    return candidates[selected]


def _wait_for_success(client: SystemTestClient, event_type: str, *, timeout_s: float) -> dict:
    return client.wait_for_event(
        lambda item: _match_success_or_raise(item, event_type),
        timeout_s=timeout_s,
    )


def _wait_for_stream_start(client: SystemTestClient) -> None:
    deadline = time.monotonic() + 90.0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Timed out waiting for official stream start.")
        event = client.wait_for_event(lambda _item: True, timeout_s=remaining)
        event_type = event.get("type")
        payload = event.get("payload", {})
        if event_type == mt.EVT_ERROR:
            raise RuntimeError(str(payload))
        if event_type == mt.EVT_STREAM_STARTED:
            print("Stream start command accepted.")
            continue
        if event_type == mt.EVT_STREAM_WARMUP_STARTED:
            print(
                "Warmup started: "
                f"attempt {payload.get('attempt')}/{payload.get('max_attempts')} "
                f"stable={payload.get('stable_sensor_count')}/{payload.get('required_sensor_count')}"
            )
            continue
        if event_type == mt.EVT_STREAM_STARTUP_RETRY:
            print(
                "Startup gate retry: "
                f"attempt {payload.get('attempt')}/{payload.get('max_attempts')} "
                f"reason={payload.get('reason')}"
            )
            continue
        if event_type == mt.EVT_STREAM_OFFICIAL_STARTED:
            print("Official streaming started.")
            return
        if event_type == mt.EVT_STREAM_STARTUP_FAILED:
            raise RuntimeError(str(payload.get("reason") or "Startup gate failed."))
        if event_type == mt.EVT_STREAM_DRAINED:
            raise RuntimeError(str(payload.get("reason") or "Stream drained before official start."))
        if event_type == mt.EVT_COMPUTE_RESULT:
            continue


def _match_success_or_raise(event: dict, expected_type: str) -> bool:
    event_type = event.get("type")
    if event_type == mt.EVT_ERROR:
        raise RuntimeError(str(event.get("payload")))
    return event_type == expected_type


def _normalize(value: object) -> str:
    return str(value or "").strip().lower()
