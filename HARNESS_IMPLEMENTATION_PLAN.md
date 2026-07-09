# Sensor Harness Implementation Plan

## Purpose

Implement the next stage of `rs-nexus-plugin-tooling` so a plugin developer can
run and validate a sensor plugin directly from source, against a real sensor,
without requiring `rs-nexus-os` or a built `.rsnxplugin` bundle.

This harness is the pre-install validation surface. The `rs-nexus-os` installer
should continue to assume the plugin artifact has already been validated.

Initial target plugin for this work:

- `dev-plugins/sensors/rs-nexus-sensor-movesense`

## Current State

Current `rsnexus-plugin test sensor` behavior is limited to:

- loading `plugin.json`
- importing the entry point from `src/`
- instantiating the sensor class
- loading the sensor spec
- probing listener registration
- probing `consume_input`

This is useful as a smoke test, but it does not behave like the runtime path a
real sensor plugin sees under `rs-nexus-os`.

## Target Outcome

Add a source-mode harness that behaves like a minimal sensor-manager/runtime
shim. It should exercise the plugin lifecycle and adapter interactions closely
enough that a developer can validate core behavior before packaging.

The harness should:

- load the plugin directly from source
- create a runtime-owned sensor instance and bind runtime state
- provide an adapter abstraction that the plugin can call
- support real hardware execution where a backend is available
- capture emitted events and summarize them for the developer
- validate setup/stream lifecycle behavior
- remain independent from `.rsnxplugin` build/install flows

## Scope Boundaries

The harness should own:

- source-tree loading
- runtime shim behavior
- lifecycle exercising
- event/sample observation
- developer diagnostics

The harness should not own:

- production installation
- activation into plugin roots
- version cataloging
- bundle deployment behavior

Separate packaging validation can be added later as a different command such as
`rsnexus-plugin validate` or `rsnexus-plugin preflight`.

## First-Class Test Target

Use Movesense as the first acceptance target:

- plugin root:
  `dev-plugins/sensors/rs-nexus-sensor-movesense`
- entry point:
  `movesense_sensor.sensor:MovesenseSensor`
- current declared runtime dependency:
  `bleak>=0.20.0`

The first milestone is not “all plugins”. The first milestone is “Movesense can
be run from source through the harness against a real sensor and the developer
can see whether setup and streaming work.”

## Proposed CLI Shape

Keep the existing command family and extend it:

```bash
rsnexus-plugin test sensor --plugin-root /path/to/plugin
```

Add options needed for runtime behavior:

```bash
rsnexus-plugin test sensor \
  --plugin-root /path/to/plugin \
  --adapter BLE \
  --address AA:BB:CC:DD:EE:FF \
  --duration 15 \
  --enable-battery \
  --enable-button
```

Likely next options:

- `--adapter BLE`
- `--address <device-address>`
- `--name <device-name>`
- `--duration <seconds>`
- `--identify`
- `--enable-battery`
- `--enable-button`
- `--location <body-location>`
- `--attribute KEY=VALUE`
- `--list-events`
- `--fail-on-no-data`

Defer multi-plugin routing until later. Phase 1 should focus on a single sensor
plugin and a single sensor instance.

## Architecture

Implement a small runtime shim inside `rs-nexus-plugin-tooling`, not by pulling
in `rs-nexus-os` modules directly.

Suggested module split:

- `packages/cli/src/rs_nexus_plugin_cli/harness.py`
  CLI entrypoint and report formatting
- `packages/cli/src/rs_nexus_plugin_cli/harness_runtime.py`
  source-loader, plugin runner, lifecycle orchestration
- `packages/cli/src/rs_nexus_plugin_cli/harness_adapter.py`
  adapter protocol and BLE-backed implementation(s)
- `packages/cli/src/rs_nexus_plugin_cli/harness_models.py`
  config, event records, result summary

## Runtime Shim Responsibilities

The shim should provide the plugin with the minimal runtime state it expects:

- a sensor-like object with `local_name`
- connection status transitions
- transport client assignment
- location assignment
- attribute overrides from CLI
- listener registration for declared events

Harness flow:

1. Load plugin manifest from source tree.
2. Import the entry point from `src/`.
3. Validate `SensorBase` subclass and spec load.
4. Instantiate the sensor class.
5. Apply location and attribute overrides.
6. Construct adapter/backend.
7. Bind discovered/selected transport client.
8. Call `setup(...)`.
9. Optionally call `identify(...)`.
10. Call `start_stream(...)`.
11. Run for configured duration while collecting events.
12. Call `stop_stream(...)`.
13. Print a validation summary and failures.

## Adapter Layer

The harness needs a narrow adapter contract that mirrors the methods plugins
actually call today.

Phase 1 adapter surface:

- `read(client, uuid)`
- `write(client, uuid, payload)`
- `set_notify_callback(client, uuid, callback)`

Likely support helpers:

- `discover(...)`
- `connect(...)`
- `disconnect(...)`

Implementation strategy:

- define a small adapter protocol in tooling
- provide a BLE implementation for source-mode testing
- keep transport/backend wiring isolated from the core harness runner

Do not try to reproduce all of `rs-nexus-os` sensor-manager behavior in the
first pass. Only implement the contract needed by migrated sensor plugins.

## Event Capture And Validation

The harness should record emitted plugin events, not just print them.

Capture at least:

- event name
- timestamp
- payload type
- payload summary

Validation rules for Phase 1:

- declared event names must be registerable
- `setup()` must complete without exception
- `start_stream()` must complete without exception
- if `--fail-on-no-data` is set, at least one `on_data` event must be emitted
- `stop_stream()` must complete without exception

Useful summary output:

- plugin id and entry point
- adapter family
- selected sensor name/address
- capabilities and declared events
- count of `on_data`, `on_error`, battery, button, and disconnect events
- first and last sample timestamps when available

## Movesense Acceptance Criteria

Phase 1 is complete when the following is true for the Movesense plugin:

1. The harness can load `dev-plugins/sensors/rs-nexus-sensor-movesense` from
   source without building.
2. The developer can target a real Movesense sensor by address or discovery.
3. The harness can call `setup()` successfully with the selected adapter.
4. The harness can start streaming and capture `on_data` events.
5. The harness can stop streaming cleanly.
6. The harness prints a summary that makes failures obvious.
7. A failed adapter operation or plugin exception produces a non-zero exit.

## Non-Goals For First Session

Do not include these in the first implementation pass:

- algorithm harness parity
- multi-plugin routing graphs
- simulated upstream plugin input networks
- bundle install into a temporary `rs-nexus-os` plugin root
- full parity with `rs_nexus_plugins.runtime.sensor_runtime`
- cloud deployment checks

## Packaging Validation Follow-On

After the source-mode harness is usable, add a separate validation command for
deployability of built artifacts.

That follow-on command should check:

- plugin manifest completeness
- build succeeds
- dependency wheels are present in the bundle
- bundle manifest/checksums are valid
- installer-compatible artifact layout is produced

This is distinct from source-mode runtime validation and should not be folded
back into `harness.py`.

## Implementation Order

### Phase 1

- refactor current harness code into loader plus runner pieces
- add runtime result models
- add lifecycle execution and event capture
- add CLI options for location, attributes, and runtime duration

### Phase 2

- add BLE adapter abstraction and concrete backend
- support selecting a real device by address or name
- validate Movesense against real hardware

### Phase 3

- tighten failure modes and exit codes
- add structured summary output
- add tests around loader, listener capture, and lifecycle orchestration

### Phase 4

- add separate packaging/deployability preflight command
- verify dependency-wheel completeness for `.rsnxplugin`

## Testing Strategy

Unit tests in `rs-nexus-plugin-tooling` should cover:

- manifest loading
- entry point import from source
- event capture
- lifecycle order enforcement
- attribute/location override application
- failure propagation when plugin hooks raise

Integration-style tests should cover:

- reference plugin smoke execution with a fake adapter
- Movesense harness execution path with a fake BLE adapter contract

Real hardware validation remains manual:

- use Movesense as the first manual validation target
- capture the exact CLI invocation that succeeds
- document required host dependencies for the chosen BLE backend

## Open Questions For Next Session

- Which BLE backend should the source harness standardize on first?
- Should device discovery be built into the harness or should Phase 1 require
  an explicit address?
- Do we want a machine-readable output mode now or after the first manual pass?
- Should the harness expose sample payload dumps, or just counts and summaries?

## Recommended Next Session Start

1. Refactor `harness.py` into loader plus runner support modules.
2. Implement event capture and lifecycle orchestration with a fake adapter.
3. Add CLI flags for `--duration`, `--location`, `--attribute`, and
   `--fail-on-no-data`.
4. Inspect the Movesense sensor implementation and define the minimum BLE
   adapter contract needed for `setup()` and streaming.

