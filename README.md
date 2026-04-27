# RS Nexus Plugin Tooling

Developer tooling for creating RS Nexus plugins.

This repository provides:

- `rs-nexus-plugin-sdk`: shared authoring contracts for RS Nexus sensor and algorithm plugins.
- `rs-nexus-plugin-cli`: the `rsnexus-plugin` command for scaffolding plugin projects.

Repository: <https://github.com/Nexus-N3/rs-nexus-plugin-tooling>

## Status

This project is in early development. The current scope is plugin authoring and
local scaffolding. Runtime installation, plugin catalog support, and isolated
plugin execution are planned for RS Nexus OS but are not implemented here yet.

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
created:

```bash
rsnexus-plugin init sensor my-sensor-plugin
```

Example with additional metadata:

```bash
rsnexus-plugin init sensor movella-dot --manufacturer-id 2182 --sample-type imu
```

This creates:

- `rs-nexus-sensor-<plugin-id>/pyproject.toml`
- `rs-nexus-sensor-<plugin-id>/plugin.json`
- `rs-nexus-sensor-<plugin-id>/src/<package>/sensor.py`
- `rs-nexus-sensor-<plugin-id>/src/<package>/samples.py`
- a sensor spec YAML file
- basic import, manifest, and spec tests

## Scaffold An Algorithm Plugin

Run the command from the directory where the plugin repository should be
created:

```bash
rsnexus-plugin init algorithm my-algorithm-plugin
```

Optional executor modules can be included:

```bash
rsnexus-plugin init algorithm generic-data-summary --with-intermediate --with-consolidation
```

This creates:

- `rs-nexus-algorithm-<plugin-id>/pyproject.toml`
- `rs-nexus-algorithm-<plugin-id>/plugin.json`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/core.py`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/core_schema.py`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/processing.py`
- `rs-nexus-algorithm-<plugin-id>/src/<package>/config.yaml`
- optional intermediate and consolidation executor modules
- basic import, manifest, and config tests

## Generated Plugin Contract

Generated plugins use:

- a `pyproject.toml` build definition
- a `plugin.json` manifest
- `src/` package layout
- `rs-nexus-plugin-sdk` contracts for base classes and shared types
- Python entry points for future runtime discovery

The current entry point groups are:

- `rs_nexus.sensors`
- `rs_nexus.algorithms`

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
