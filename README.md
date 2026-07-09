# RS Nexus Plugin Tooling

Developer tooling for creating, preparing, testing, and packaging RS Nexus plugins.

This repository provides the shared SDK and CLI used to author RS Nexus sensor and algorithm plugins.

Repository:

```text
https://github.com/Nexus-N3/rs-nexus-plugin-tooling
```

## Overview

This repository provides:

* `rs-nexus-plugin-sdk`: shared authoring contracts for RS Nexus plugins
* `rs-nexus-plugin-cli`: the `rsnexus-plugin` command-line tool
* scaffolding for sensor and algorithm plugins
* isolated per-plugin environment creation
* local source-tree validation
* Phase 1 `.rsnxplugin` bundle packaging compatible with `rs-nexus-os`
* a focused sensor-plugin harness for source-tree development checks

The main idea is simple:

```text
Install the plugin tooling once.
Use rsnexus-plugin to create plugins.
Each plugin gets its own isolated .venv.
Build and test commands use the plugin's own .venv.
The CLI is not installed into every plugin .venv.
```

## Status

This project is in early development.

The current implemented scope is:

* plugin scaffolding
* local source-tree validation
* Phase 1 `.rsnxplugin` bundle packaging for `rs-nexus-os`

Live isolated plugin runtime execution still belongs to `rs-nexus-os`.

`rs-nexus-plugin-tooling` owns the developer-side workflow for creating and building plugins.

`rs-nexus-os` owns plugin installation, cataloging, runtime discovery, and runtime execution.

## Environment Model

RS Nexus plugin development uses three separate environments.

### 1. Tooling Environment

The tooling environment belongs to this repository.

Example location:

```text
rs-nexus-plugin-tooling/.venv
```

It contains:

* the `rsnexus-plugin` CLI
* the plugin SDK source
* scaffold/build/test orchestration code

It is used to:

* scaffold plugins
* create plugin environments
* launch plugin builds
* run plugin validation commands

The tooling environment is installed once.

### 2. Plugin Environment

Each plugin owns its own isolated Python environment.

Example location:

```text
dev-plugins/sensors/rs-nexus-sensor-movella-dot/.venv
```

It contains:

* the plugin package
* the plugin's runtime dependencies
* the plugin's build dependencies
* the RS Nexus plugin SDK dependency required by the plugin

It is used to:

* develop the plugin
* test the plugin
* build the plugin wheel
* collect dependencies for `.rsnxplugin` bundles

Each plugin gets its own `.venv` to avoid dependency conflicts between plugins.

The `rsnexus-plugin` CLI should not be installed into every plugin `.venv`.

### 3. Runtime Environment

The runtime environment belongs to `rs-nexus-os`.

Example location:

```text
rs-nexus-os/.venv
```

It contains:

* `rs-nexus-os`
* installed `.rsnxplugin` bundles
* plugin discovery and runtime execution code

It is used to:

* install plugin bundles
* discover installed plugins
* run plugins inside RS Nexus OS

## Recommended Workspace Layout

Recommended layout:

```text
<workspace>/
  rs-nexus-plugin-tooling/
  rs-nexus-os/
  dev-plugins/
    sensors/
    algorithms/
    plugin-builds/
      sensors/
      algorithms/
```

Example:

```text
rs-nexus-project/
  rs-nexus-plugin-tooling/
  rs-nexus-os/
  dev-plugins/
    sensors/
      rs-nexus-sensor-movella-dot/
        .venv/
    algorithms/
      rs-nexus-algorithm-standard-loading-intensity/
        .venv/
    plugin-builds/
      sensors/
      algorithms/
```

Directory conventions:

* sensor plugin repositories live under `dev-plugins/sensors/`
* algorithm plugin repositories live under `dev-plugins/algorithms/`
* built sensor bundles go under `dev-plugins/plugin-builds/sensors/`
* built algorithm bundles go under `dev-plugins/plugin-builds/algorithms/`

## Requirements

* Python 3.10 or newer
* Python `venv` support
* `pip`
* `git`

## Install The Tooling

Clone this repository and run the installer:

```bash
git clone https://github.com/Nexus-N3/rs-nexus-plugin-tooling.git
cd rs-nexus-plugin-tooling
./install.sh
```

The installer creates or reuses `.venv` inside the tooling repository.

It installs the SDK and CLI in editable mode and validates that `rsnexus-plugin` can start.

Activate the tooling environment:

```bash
source .venv/bin/activate
rsnexus-plugin --help
```

Alternatively, add the tooling environment to your `PATH`:

```bash
export PATH="/path/to/rs-nexus-plugin-tooling/.venv/bin:$PATH"
rsnexus-plugin --help
```

To install into a different tooling virtual environment path:

```bash
RS_NEXUS_PLUGIN_TOOLING_VENV=/path/to/venv ./install.sh
```

To choose a specific Python executable:

```bash
PYTHON=/path/to/python3 ./install.sh
```

## Current Workflow

The intended workflow is:

```text
1. Install rs-nexus-plugin-tooling once.

2. Use rsnexus-plugin init to scaffold a plugin.

3. The init command creates the plugin source tree and the plugin's isolated .venv.

4. Edit the plugin code as needed.

5. Build a .rsnxplugin bundle using rsnexus-plugin build.

6. Install the bundle into rs-nexus-os.

7. Run rs-nexus-os, which discovers installed plugins from the configured plugin root.
```

The tooling CLI is shared.

The plugin `.venv` is isolated.

The runtime consumes the final bundle.

## One-Time Workspace Setup

Create the shared development directories:

```bash
mkdir -p /path/to/dev-plugins/sensors
mkdir -p /path/to/dev-plugins/algorithms
mkdir -p /path/to/dev-plugins/plugin-builds/sensors
mkdir -p /path/to/dev-plugins/plugin-builds/algorithms
```

## Scaffold A Sensor Plugin

Run the command from anywhere using the shared tooling CLI:

```bash
rsnexus-plugin init sensor movella-dot --output-dir /path/to/dev-plugins
```

When `--output-dir` points at the shared `dev-plugins` workspace, sensor plugins are placed under:

```text
dev-plugins/sensors/
```

Example with additional metadata:

```bash
rsnexus-plugin init sensor movella-dot \
  --output-dir /path/to/dev-plugins \
  --manufacturer-id 2182 \
  --sample-type imu
```

This creates the plugin source tree and its isolated `.venv`.

Example output:

```text
dev-plugins/
  sensors/
    rs-nexus-sensor-movella-dot/
      .venv/
      pyproject.toml
      plugin.json
      src/
        rs_nexus_sensor_movella_dot/
          plugin.json
          sensor.py
          samples.py
      tests/
      specs/
```

Canonical sensor naming:

```text
repo name:
  rs-nexus-sensor-<plugin-id>

Python package:
  rs_nexus_sensor_<plugin_id>
```

`--package-name` remains available as an override, but the default convention is the expected layout for new sensor plugins.

## Scaffold An Algorithm Plugin

Run the command from anywhere using the shared tooling CLI:

```bash
rsnexus-plugin init algorithm standard-loading-intensity --output-dir /path/to/dev-plugins
```

When `--output-dir` points at the shared `dev-plugins` workspace, algorithm plugins are placed under:

```text
dev-plugins/algorithms/
```

Intermediate and consolidation executor files are always scaffolded.

By default, their schedules are disabled and the generated executor classes are no-op placeholders.

Use these flags when you want the scaffold to enable those stages in `plugin.json` and `config.yaml` and provide example implementations:

```bash
rsnexus-plugin init algorithm generic-data-summary \
  --output-dir /path/to/dev-plugins \
  --with-intermediate \
  --with-consolidation
```

This creates the plugin source tree and its isolated `.venv`.

Example output:

```text
dev-plugins/
  algorithms/
    rs-nexus-algorithm-generic-data-summary/
      .venv/
      pyproject.toml
      plugin.json
      src/
        rs_nexus_algorithm_generic_data_summary/
          plugin.json
          core.py
          core_schema.py
          processing.py
          config.yaml
          intermediate_executor.py
          consolidation_executor.py
      tests/
```

Canonical algorithm naming:

```text
repo name:
  rs-nexus-algorithm-<plugin-id>

Python package:
  rs_nexus_algorithm_<plugin_id>
```

## What `init` Does

The `init` command is responsible for creating a usable plugin development repository.

It should:

```text
1. Create the plugin directory.

2. Write the standard plugin source layout.

3. Write pyproject.toml.

4. Write plugin.json.

5. Write package-level plugin metadata.

6. Write starter tests.

7. Create <plugin-root>/.venv.

8. Install or upgrade pip.

9. Install setuptools, wheel, and build.

10. Install the local RS Nexus plugin SDK into the plugin .venv.

11. Install the generated plugin package into the plugin .venv.
```

The plugin `.venv` belongs to the plugin.

The tooling `.venv` belongs to the shared CLI.

The CLI should not need to be installed into the plugin `.venv`.

## Plugin Dependencies

Each plugin declares and owns its own dependencies.

Those dependencies should be installed into the plugin's own `.venv`.

For example, an algorithm plugin may need:

```bash
cd /path/to/dev-plugins/algorithms/rs-nexus-algorithm-example
source .venv/bin/activate
python -m pip install numpy scipy
```

A sensor plugin may need different dependencies:

```bash
cd /path/to/dev-plugins/sensors/rs-nexus-sensor-example
source .venv/bin/activate
python -m pip install pydantic
```

Only install the dependencies required by that plugin.

Do not use a shared plugin development environment for multiple plugins.

## Build A Plugin Bundle

The build command produces a Phase 1 `.rsnxplugin` ZIP bundle compatible with the `rs_nexus_plugins` installer in `rs-nexus-os`.

Basic usage:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --output-dir /path/to/plugin-builds
```

Sensor example:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/dev-plugins/sensors/rs-nexus-sensor-movella-dot \
  --output-dir /path/to/dev-plugins/plugin-builds/sensors
```

Algorithm example:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity \
  --output-dir /path/to/dev-plugins/plugin-builds/algorithms
```

The build command should use the plugin's own environment:

```text
<plugin-root>/.venv
```

It should not depend on whichever virtual environment is active in the shell.

Conceptually:

```text
rsnexus-plugin build
  -> locate plugin root
  -> locate plugin .venv
  -> use <plugin-root>/.venv/bin/python
  -> build the plugin wheel
  -> include the SDK wheel
  -> collect bundle artifacts
  -> write .rsnxplugin
```

If the plugin environment is missing, the CLI should report a clear error:

```text
Plugin environment not found.

Expected:
  <plugin-root>/.venv

This usually means the plugin was not created with rsnexus-plugin init
or the environment has been deleted.
```

## Build Output

Example output:

```text
/path/to/dev-plugins/plugin-builds/sensors/
  rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin
```

The `.rsnxplugin` archive is a normal ZIP container.

It contains:

```text
manifest.json
checksums.json
artifacts/
  plugin wheel
  SDK wheel
metadata/
  optional copied metadata
```

Depending on the plugin type, metadata may include:

* sensor spec files
* algorithm config files
* other plugin-declared metadata

## Dependency Bundling

Each plugin `.venv` is the source of truth for that plugin's dependency set.

This avoids dependency conflicts between plugins.

A plugin with one version of a dependency and another plugin with a different version should be able to build independently because each has its own environment.

The bundle process should support two modes.

### Source Bundle / Runtime-Resolved Dependencies

The bundle includes:

```text
- plugin wheel
- SDK wheel
- manifest
- checksums
- metadata
```

Third-party dependencies are expected to be resolved by the target runtime environment.

### Dependency-Complete Bundle

The bundle includes:

```text
- plugin wheel
- SDK wheel
- third-party dependency wheels
- manifest
- checksums
- metadata
```

This is preferred for offline or controlled deployments.

Expected command:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --output-dir /path/to/plugin-builds \
  --include-dependencies
```

Manual artifact inclusion should remain supported:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --output-dir /path/to/plugin-builds \
  --artifact /path/to/dist/numpy.whl \
  --artifact /path/to/dist/scipy.whl
```

## SDK Handling

Generated plugins use `rs-nexus-plugin-sdk` contracts for base classes and shared types.

During `init`, the plugin `.venv` should install the SDK from the local tooling checkout.

During bundle creation, the CLI should include an SDK wheel when it can resolve the SDK source.

If needed, point explicitly at the SDK source:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --output-dir /path/to/plugin-builds \
  --sdk-root /path/to/rs-nexus-plugin-tooling/packages/sdk
```

Use `--no-sdk` only when you intentionally do not want the SDK wheel included.

## Install A Built Bundle Into RS Nexus OS

After building a bundle, install it from `rs-nexus-os`:

```bash
cd /path/to/rs-nexus-os

python -m rs_nexus_plugins install \
  /path/to/dev-plugins/plugin-builds/sensors/rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin
```

For local development against `dev-plugins`, `rs-nexus-os` also provides:

```bash
python -m rs_nexus_plugins install-dev \
  --dev-plugins-root /path/to/dev-plugins \
  --plugin movella-dot
```

List local development plugins:

```bash
python -m rs_nexus_plugins install-dev-list
```

`rs-nexus-plugin-tooling` builds bundles.

`rs-nexus-os` installs and runs bundles.

## Generated Plugin Contract

Generated plugins use:

* a `pyproject.toml` build definition
* a root-level `plugin.json` manifest for source review
* a packaged `src/<package>/plugin.json` manifest included in the built wheel
* a `src/` package layout
* `rs-nexus-plugin-sdk` contracts for base classes and shared types
* Python entry points for future runtime discovery

Current entry point groups are:

```text
rs_nexus.sensors
rs_nexus.algorithms
```

## Algorithm Plugin Contract

Algorithm plugins may include:

* core processing code
* schema definitions
* processing helpers
* intermediate executor
* consolidation executor
* plugin config

Executor file presence is not the capability contract.

Runtime support for intermediate and consolidation stages is declared by:

```text
plugin.json
config.yaml
```

For example:

```text
plugin.json:
  supports_intermediate
  supports_consolidation

config.yaml:
  schedules.intermediate.enabled
  schedules.consolidated.enabled
```

`rs-nexus-os` should use those declarations when deciding whether to schedule or load optional executor stages.

## Sensor Plugin Contract

Sensor plugins may declare and implement a `consume_input` hook when they accept forwarded data from another sensor plugin through the runtime.

Algorithm plugins already receive per-sensor data through their existing sample pipeline.

Sensor plugins should not need to depend directly on BLE backends such as `bleak` for normal packaging.

Runtime BLE operations belong to `rs-nexus-os` today and to the future harness adapter layer when source-mode testing is added.

## Test A Sensor Plugin

To validate a sensor plugin while developing it, without booting the full server:

```bash
rsnexus-plugin test sensor \
  --plugin-root /path/to/dev-plugins/sensors/rs-nexus-sensor-example
```

The harness should use the plugin's own `.venv`.

The harness:

```text
- loads the plugin from src/
- resolves the manifest entry point
- instantiates the sensor class
- validates spec/listener wiring
- probes the optional consume_input hook
```

If the plugin `.venv` is missing, the plugin should be recreated or the environment should be repaired.

The normal path is for `rsnexus-plugin init` to create the `.venv`.

## Reference Plugin Examples

Current reference migration plugins:

```text
Sensor:
  dev-plugins/sensors/rs-nexus-sensor-movella-dot

Algorithm:
  dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity
```

Build sensor example:

```bash
rsnexus-plugin build \
  --plugin-root ./dev-plugins/sensors/rs-nexus-sensor-movella-dot \
  --output-dir ./dev-plugins/plugin-builds/sensors
```

Build algorithm example:

```bash
rsnexus-plugin build \
  --plugin-root ./dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity \
  --output-dir ./dev-plugins/plugin-builds/algorithms
```

Expected outputs:

```text
dev-plugins/plugin-builds/sensors/
  rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin

dev-plugins/plugin-builds/algorithms/
  rs-nexus-algorithm-standard-loading-intensity-0.1.0.rsnxplugin
```

## Developer Commands Summary

Install tooling once:

```bash
cd /path/to/rs-nexus-plugin-tooling
./install.sh
source .venv/bin/activate
```

Scaffold a sensor plugin:

```bash
rsnexus-plugin init sensor movella-dot --output-dir /path/to/dev-plugins
```

Scaffold an algorithm plugin:

```bash
rsnexus-plugin init algorithm standard-loading-intensity --output-dir /path/to/dev-plugins
```

Build a sensor plugin:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/dev-plugins/sensors/rs-nexus-sensor-movella-dot \
  --output-dir /path/to/dev-plugins/plugin-builds/sensors
```

Build an algorithm plugin:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity \
  --output-dir /path/to/dev-plugins/plugin-builds/algorithms
```

Install bundle into RS Nexus OS:

```bash
cd /path/to/rs-nexus-os

python -m rs_nexus_plugins install \
  /path/to/dev-plugins/plugin-builds/sensors/rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin
```

## Important Design Rule

Do not require this:

```bash
cd /path/to/plugin
source .venv/bin/activate
pip install -e /path/to/rs-nexus-plugin-tooling/packages/cli
```

The plugin `.venv` is for the plugin and its dependencies.

The tooling `.venv` is for the shared CLI.

The CLI should call into the plugin `.venv` when it needs to build or test the plugin.

## Development Notes

The SDK and CLI packages currently use `setup.py` because editable local installs are the main development workflow.

Scaffolded plugin projects use `pyproject.toml`.

The build path should avoid relying on the caller's active Python environment.

Preferred behavior:

```text
rsnexus-plugin build
  uses <plugin-root>/.venv/bin/python
```

Avoid this behavior:

```text
rsnexus-plugin build
  uses whichever python happens to be active in the shell
```

This makes the build process more predictable and keeps plugin dependencies isolated.

## Files Not To Commit

Do not commit local runtime artifacts.

Examples:

```text
.venv/
__pycache__/
*.pyc
build/
dist/
*.egg-info/
plugin-build/
*.rsnxplugin
```

These should be covered by `.gitignore`.

## Security

This repository should not contain:

* device credentials
* cloud connection strings
* SAS tokens
* API keys
* private keys
* site-specific configuration
* customer-specific deployment configuration

If a generated plugin needs deployment credentials or runtime configuration, provide those through the target runtime environment rather than committing them to the plugin source repository.

## Ownership Boundary

```text
rs-nexus-plugin-tooling
  creates, prepares, validates, and builds plugins

plugin repositories
  contain plugin code, manifests, configs, tests, and isolated dependencies

rs-nexus-os
  installs, catalogs, discovers, and runs plugins
```

This boundary should stay clear.

The tooling should make plugin development easy.

The plugin environment should keep dependencies isolated.

The runtime should consume built bundles.
