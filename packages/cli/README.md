# RS Nexus Plugin CLI

Developer CLI for scaffolding, packaging, and locally testing RS Nexus plugins.

The current primary workflow is:

1. scaffold or edit a plugin source tree
2. build a `.rsnxplugin` bundle with `rsnexus-plugin build`
3. install that bundle using `rs_nexus_plugins` in `rs-nexus-os`

## Commands

```bash
rsnexus-plugin init sensor my-sensor-plugin
rsnexus-plugin init algorithm my-algorithm-plugin
rsnexus-plugin init algorithm my-algorithm-plugin --with-intermediate --with-consolidation
rsnexus-plugin build --plugin-root /path/to/plugin --output-dir /tmp/plugin-build
```

Run this from the directory where the plugin repository should be created.
The CLI must be installed in the active Python environment or otherwise
available on `PATH`.

For sensor plugins, the canonical scaffold layout is:

- repo: `rs-nexus-sensor-<plugin-id>`
- Python package: `rs_nexus_sensor_<plugin_id>`

Recommended workflow:

- install the shared tooling once with `./install.sh`
- keep `rsnexus-plugin` on `PATH`, for example through `~/.local/bin`
- create a `.venv` inside each plugin repository
- let `rsnexus-plugin init` manage the plugin `.venv`

This keeps plugin dependencies isolated while keeping the CLI and sensor
harness outside plugin environments.

Algorithm scaffolds always include `intermediate_executor.py` and
`consolidation_executor.py`. The `--with-intermediate` and
`--with-consolidation` flags enable those stages in the generated manifest and
config; without the flags, the executor files are disabled no-op placeholders.

From the tooling repo root, run:

```bash
./install.sh
```

This creates or reuses the tooling `.venv`, installs the CLI there, and writes
a `rsnexus-plugin` launcher into `~/.local/bin` by default.

## Sensor Test Harness

Use the shared CLI to execute a sensor plugin test run:

```bash
rsnexus-plugin test sensor --plugin-root /path/to/plugin
```

The CLI harness launches the plugin's own `.venv/bin/python` for the runtime
portion, so plugin dependencies stay isolated even though the harness lives in
the tooling environment.

## Build Output

`rsnexus-plugin build` produces a Phase 1 `.rsnxplugin` ZIP archive for
`rs-nexus-os`.

Basic usage:

```bash
rsnexus-plugin build --plugin-root /path/to/plugin --output-dir /tmp/plugin-build
```

This writes the final bundle into the directory passed by `--output-dir`.

When omitted, the CLI default is `plugin-build/`. This is intentional so the
final `.rsnxplugin` output does not collide with Python build working
directories such as `build/`.

If you want to keep the bundle for deployment or repeated installs, use a
persistent output directory rather than `/tmp`.

Example output:

```text
/tmp/plugin-build/rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin
```

The build command produces:

- a plugin wheel
- the local `rs-nexus-plugin-sdk` wheel when it can be resolved
- `manifest.json`
- `checksums.json`
- a final `.rsnxplugin` archive

The archive is a normal ZIP container with:

- `manifest.json` at archive root
- `checksums.json` at archive root
- wheel artifacts under `artifacts/`
- optional copied metadata under `metadata/`

## Third-Party Wheels

The build command does **not** fetch third-party dependency wheels and place
them into the bundle automatically.

In practice this means packages such as:

- `numpy`
- `scipy`
- any other plugin dependency not already represented by a local wheel you pass

will still be declared in the plugin wheel metadata, but their wheel files will
not be embedded in the `.rsnxplugin` unless you include them explicitly.

Why this matters:

- the Phase 1 installer in `rs-nexus-os` installs bundle artifacts into the
  plugin `.venv`
- for a connected or pre-provisioned environment, dependencies may already be
  available through the target environment or other local wheel sources
- for a truly offline transfer/install workflow, every required wheel must be
  physically present in the `.rsnxplugin`

So “offline-complete bundle” means:

- the plugin wheel is inside the bundle
- the SDK wheel is inside the bundle if required
- every third-party dependency wheel needed at install time is also inside the
  bundle

To do that, pass repeated `--artifact` arguments:

```bash
rsnexus-plugin build \
  --plugin-root /path/to/plugin \
  --output-dir /tmp/plugin-build \
  --artifact /path/to/wheels/numpy-<version>-py3-none-any.whl \
  --artifact /path/to/wheels/scipy-<version>-py3-none-any.whl
```

You can also point directly at the local SDK source with `--sdk-root`.

Because the build path uses `python -m build --no-isolation`, it is intended
for prepared local development environments rather than fresh network-dependent
build environments.

## Reference Examples

The current reference migration plugins are:

- sensor:
  `dev-plugins/sensors/rs-nexus-sensor-movella-dot`
- algorithm:
  `dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity`

Example commands:

```bash
rsnexus-plugin build \
  --plugin-root ./dev-plugins/sensors/rs-nexus-sensor-movella-dot \
  --output-dir /tmp/rsnx-build-sensor
```

```bash
rsnexus-plugin build \
  --plugin-root ./dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity \
  --output-dir /tmp/rsnx-build-algo
```

These produce `.rsnxplugin` bundles compatible with the Phase 1 installer in
`rs-nexus-os/rs_nexus_plugins`.

Install example:

```bash
cd /path/to/rs-nexus-os
python -m rs_nexus_plugins install /tmp/rsnx-build-sensor/rs-nexus-sensor-movella-dot-0.1.0.rsnxplugin
```

For local development driven by `config/runtime.env`, `rs-nexus-os` also
provides:

```bash
python -m rs_nexus_plugins show-dev-list
python -m rs_nexus_plugins install-dev-list
```
