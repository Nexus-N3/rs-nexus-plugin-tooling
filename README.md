# RS Nexus Plugin Tooling

Developer tooling for creating and packaging RS Nexus plugins.

This repository provides:

- `rs-nexus-plugin-sdk`: shared authoring contracts for RS Nexus sensor and algorithm plugins.
- `rs-nexus-plugin-cli`: the `rsnexus-plugin` command for scaffolding plugin projects.
- a Phase 1 `.rsnxplugin` bundle build path compatible with `rs-nexus-os`
- a focused sensor-plugin harness for source-tree development checks

Repository: <https://github.com/Nexus-N3/rs-nexus-plugin-tooling>

## Status

This project is in early development. The current implemented scope is:

- plugin scaffolding
- local source-tree validation
- Phase 1 `.rsnxplugin` bundle packaging for `rs-nexus-os`

Live isolated plugin runtime execution still belongs to `rs-nexus-os`.

## Current Workflow

The intended plugin workflow is now:

1. Scaffold or edit a plugin in `dev-plugins/`
2. Build a `.rsnxplugin` bundle with `rsnexus-plugin build`
3. Install that bundle with `python -m rs_nexus_plugins install ...` in
   `rs-nexus-os`, or use `install-dev` / `install-dev-list` there for local
   development
4. Run `rs-nexus-os`, which discovers installed plugins from the configured
   plugin root

`rs-nexus-plugin-tooling` is the build side of this workflow.
`rs-nexus-os` owns installation, cataloging, and runtime discovery.

## Requirements

- Python 3.10 or newer
- `venv` support for your Python installation
- `pip`

## Install

Clone the repository and run the installer:

```bash
git clone https://github.com/Nexus-N3/rs-nexus-plugin-tooling.git
cd rs-nexus-plugin-tooling
./install.sh
```

The installer creates or reuses `.venv` in the repository, installs the SDK and
CLI in editable mode, and validates that `rsnexus-plugin` can start.

Use the CLI by activating the virtual environment:

```bash
source .venv/bin/activate
rsnexus-plugin --help
```

Alternatively, add the tooling virtual environment to `PATH`:

```bash
export PATH="$PWD/.venv/bin:$PATH"
rsnexus-plugin --help
```

To install into a different virtual environment path:

```bash
RS_NEXUS_PLUGIN_TOOLING_VENV=/path/to/venv ./install.sh
```

To choose a specific Python executable:

```bash
PYTHON=/path/to/python3 ./install.sh
```

## Scaffold A Sensor Plugin

Run the command from the directory where the plugin repository should be
created. When `--output-dir` points at a shared `dev-plugins` workspace, sensor
plugins are placed under `dev-plugins/sensors/` automatically:

```bash
rsnexus-plugin init sensor my-sensor-plugin
rsnexus-plugin init sensor movella-dot --output-dir /path/to/dev-plugins
```

Example with additional metadata:

```bash
rsnexus-plugin init sensor movella-dot --manufacturer-id 2182 --sample-type imu
```

This creates:

- `rs-nexus-sensor-<plugin-id>/pyproject.toml`
- `rs-nexus-sensor-<plugin-id>/plugin.json`
- `rs-nexus-sensor-<plugin-id>/src/<package>/plugin.json`
- `rs-nexus-sensor-<plugin-id>/src/<package>/sensor.py`
- `rs-nexus-sensor-<plugin-id>/src/<package>/samples.py`
- a sensor spec YAML file
- basic import, manifest, and spec tests

## Scaffold An Algorithm Plugin

Run the command from the directory where the plugin repository should be
created. When `--output-dir` points at a shared `dev-plugins` workspace,
algorithm plugins are placed under `dev-plugins/algorithms/` automatically:

```bash
rsnexus-plugin init algorithm my-algorithm-plugin
rsnexus-plugin init algorithm generic-data-summary --output-dir /path/to/dev-plugins
```

Intermediate and consolidation executor files are always scaffolded. By default,
their schedules are disabled and the generated executor classes are no-op
placeholders. Use these flags when you want the scaffold to enable those stages
in `plugin.json` and `config.yaml` and provide example implementations:

```bash
rsnexus-plugin init algorithm generic-data-summary --with-intermediate --with-consolidation
```

This creates:

- `rs-nexus-algorithm-<plugin-id>/pyproject.toml`
- `rs-nexus-algorithm-<plugin-id>/plugin.json`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/plugin.json`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/core.py`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/core_schema.py`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/processing.py`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/config.yaml`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/intermediate_executor.py`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/consolidation_executor.py`
- basic import, manifest, and config tests

## Generated Plugin Contract

Generated plugins use:

- a `pyproject.toml` build definition
- a root-level `plugin.json` manifest for source review
- a packaged `src/<package>/plugin.json` manifest included in the built wheel
- `src/` package layout
- `rs-nexus-plugin-sdk` contracts for base classes and shared types
- Python entry points for future runtime discovery

For algorithm plugins, executor file presence is not the capability contract.
Runtime support for intermediate and consolidation stages is declared by:

- `plugin.json` fields such as `supports_intermediate` and `supports_consolidation`
- `config.yaml` schedule entries such as `schedules.intermediate.enabled`
  and `schedules.consolidated.enabled`

RS Nexus OS should use those declarations when deciding whether to schedule or
load optional executor stages.

Sensor plugins may declare and implement a `consume_input` hook when they
accept forwarded data from another sensor plugin via the runtime. Algorithm
plugins already receive per-sensor data through their existing sample pipeline.

The current entry point groups are:

- `rs_nexus.sensors`
- `rs_nexus.algorithms`

## Build A Phase 1 `.rsnxplugin`

The `build` command now produces a Phase 1 `.rsnxplugin` ZIP bundle compatible
with the `rs_nexus_plugins` installer in `rs-nexus-os`.

Basic usage:

```bash
rsnexus-plugin build --plugin-root /path/to/plugin --output-dir /tmp/plugin-build
```

This writes the final bundle into the directory passed by `--output-dir`.

Use a persistent output directory when you want the produced artifacts retained
for later install, transfer, or deployment. For example:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --output-dir /path/to/plugin-builds/sensors
```

Example output:

```text
/tmp/plugin-build/rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin
```

This builds:

- the plugin wheel
- the local `rs-nexus-plugin-sdk` wheel when it can be resolved
- a `manifest.json`
- a `checksums.json`
- a `.rsnxplugin` archive

The archive is a normal ZIP container with:

- `manifest.json` at archive root
- `checksums.json` at archive root
- wheel artifacts under `artifacts/`
- optional copied metadata such as sensor spec or algorithm config under `metadata/`

Important current behavior:

- the local SDK wheel is included automatically when it can be resolved
- third-party dependency wheels such as `numpy` and `scipy` are **not**
  auto-fetched into the bundle
- for an offline-complete bundle, you must provide those extra wheels explicitly
  with `--artifact`

For offline or dependency-complete bundles, add extra wheel artifacts:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --output-dir /tmp/plugin-build \
  --artifact /path/to/dist/numpy.whl \
  --artifact /path/to/dist/scipy.whl
```

If you need to point explicitly at the SDK source repo:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --sdk-root /path/to/rs-nexus-plugin-tooling/packages/sdk
```

Use `--no-sdk` only when you intentionally do not want the SDK wheel included.

Use an already prepared target runtime for this command, typically the
`rs-nexus-os` virtual environment that already has `pip`, `setuptools`, and
wheel build support available.

## Install The Built Bundle

After building a bundle, install it from `rs-nexus-os`:

```bash
cd /path/to/rs-nexus-os
python -m rs_nexus_plugins install /path/to/plugin-builds/sensors/rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin
```

For local development against `dev-plugins`, `rs-nexus-os` also provides:

```bash
python -m rs_nexus_plugins install-dev --dev-plugins-root /path/to/dev-plugins --plugin movella-dot
python -m rs_nexus_plugins install-dev-list
```

Because the build path uses `python -m build --no-isolation`, it is intended
for prepared local development environments rather than fresh network-dependent
build environments.

## Reference Plugin Examples

The current reference migration plugins are:

- sensor:
  `dev-plugins/sensors/rs-nexus-sensor-movella-dot`
- algorithm:
  `dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity`

Example commands:

```bash
rsnexus-plugin build \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-movella-dot \
  --output-dir /tmp/rsnx-build-sensor
```

```bash
rsnexus-plugin build \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity \
  --output-dir /tmp/rsnx-build-algo
```

These produce:

- `/tmp/rsnx-build-sensor/rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin`
- `/tmp/rsnx-build-algo/rs-nexus-algorithm-standard-loading-intensity-0.1.0.rsnxplugin`

Those bundles are compatible with the Phase 1 installer implemented in
`rs-nexus-os/rs_nexus_plugins`.

## Sensor Harness

To validate a sensor plugin while developing it, without booting the full
server, run the focused harness from the plugin source tree:

```bash
rsnexus-plugin test sensor --plugin-root /path/to/dev-plugins/sensors/rs-nexus-sensor-example
```

The harness:

- loads the plugin from `src/`
- resolves the manifest entry point
- instantiates the sensor class
- validates spec/listener wiring
- probes the optional `consume_input` hook

## Development Notes

The SDK and CLI packages currently use `setup.py` because editable local
installs are the main development workflow. Scaffolded plugin projects use
`pyproject.toml`.

Do not commit local runtime artifacts such as `.venv`, `__pycache__`, build
outputs, or editable-install metadata. These are covered by `.gitignore`.

## Security

This repository should not contain device credentials, cloud connection strings,
SAS tokens, API keys, private keys, or site-specific configuration.

If a generated plugin needs deployment credentials or runtime configuration,
provide those through the target runtime environment rather than committing them
to the plugin source repository.
