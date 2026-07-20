# Nexus N3 Plugin CLI

Developer CLI for scaffolding, packaging, and locally testing Nexus N3 plugins.

The current primary workflow is:

1. scaffold or edit a plugin source tree
2. build a `.rsnxplugin` bundle with `nexus-n3-plugin build`
3. install that bundle using `nexus_n3.plugins` in `nexus-n3-core`

## Commands

```bash
nexus-n3-plugin init sensor my-sensor-plugin
nexus-n3-plugin init algorithm my-algorithm-plugin
nexus-n3-plugin init algorithm my-algorithm-plugin --with-intermediate --with-consolidation
nexus-n3-plugin build --plugin-root /path/to/plugin --output-dir /tmp/plugin-build
```

Run this from the directory where the plugin repository should be created.
The CLI must be installed in the active Python environment or otherwise
available on `PATH`.

For sensor plugins, the canonical scaffold layout is:

- repo: `nexus-n3-sensor-<plugin-id>`
- Python package: `nexus_n3_sensor_<plugin_id>`

Recommended workflow:

- install the shared tooling once with `./install.sh`
- keep `nexus-n3-plugin` on `PATH`, for example through `~/.local/bin`
- create a `.venv` inside each plugin repository
- let `nexus-n3-plugin init` manage the plugin `.venv`

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
a `nexus-n3-plugin` launcher into `~/.local/bin` by default.

## Sensor Test Harness

Use the shared CLI to execute a sensor plugin test run:

```bash
nexus-n3-plugin test sensor --plugin-root /path/to/plugin
```

The CLI harness runs in the tooling environment and adds the plugin `.venv`
site-packages for the runtime portion, so plugin dependencies stay isolated
even though the harness lives in the tooling environment.

To test a built `.rsnxplugin` bundle instead of source mode:

```bash
nexus-n3-plugin test sensor-bundle --bundle-path /path/to/plugin-build/your-plugin.rsnxplugin
```

Algorithm plugins can be tested in source mode against a chosen sensor plugin:

```bash
nexus-n3-plugin test algorithm \
  --plugin-root /path/to/nexus-n3-plugin-catalog/algorithms/nexus-n3-algorithm-your-algo \
  --sensor-plugin-root /path/to/nexus-n3-plugin-catalog/sensors/nexus-n3-sensor-movesense
```

The algorithm harness reuses the reduced sensor-manager path to stream sensor
samples, then routes those samples through a reduced compute-manager path. It
prints compute events to the terminal and writes JSONL output under
`<algorithm-plugin-root>/plugin-test/computed/`.

This mirrors `nexus-n3-core` at the compute-result contract level:

- samples are ingested into a compute-manager style path
- results are routed by `stage` into `real_time`, `intermediate_time`, and
  `consolidated_time`
- algorithm-specific payload bodies are allowed to differ between plugins

The harness does not impose a single algorithm payload schema. It aligns to the
existing `nexus-n3-core` expectation that `stage` and compute-result routing are
consistent, while result contents remain algorithm-specific.

To use a built sensor bundle as the input source, replace
`--sensor-plugin-root` with `--sensor-bundle-path`.

To test a built algorithm bundle instead of source mode:

```bash
nexus-n3-plugin test algorithm-bundle \
  --bundle-path /path/to/plugin-build/your-algorithm.rsnxplugin \
  --sensor-bundle-path /path/to/plugin-build/your-sensor.rsnxplugin
```

## Build Output

`nexus-n3-plugin build` produces a Phase 1 `.rsnxplugin` ZIP archive for
`nexus-n3-core`.

Basic usage:

```bash
nexus-n3-plugin build --plugin-root /path/to/plugin --output-dir /tmp/plugin-build
```

This writes the final bundle into the directory passed by `--output-dir`.

If a bundle with the same filename already exists in that directory, it is
replaced automatically.

When omitted, the CLI default is `plugin-build/`. This is intentional so the
final `.rsnxplugin` output does not collide with Python build working
directories such as `build/`.

If you want to keep the bundle for deployment or repeated installs, use a
persistent output directory rather than `/tmp`.

Example output:

```text
/tmp/plugin-build/nexus-n3-sensor-movella-dot-0.1.0.rsnxplugin
```

The build command produces:

- a plugin wheel
- the local `nexus-n3-plugin-sdk` wheel when it can be resolved
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

- the Phase 1 installer in `nexus-n3-core` installs bundle artifacts into the
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
nexus-n3-plugin build \
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
  `nexus-n3-plugin-catalog/sensors/nexus-n3-sensor-movella-dot`
- algorithm:
  `nexus-n3-plugin-catalog/algorithms/nexus-n3-algorithm-standard-loading-intensity`

Example commands:

```bash
nexus-n3-plugin build \
  --plugin-root ./nexus-n3-plugin-catalog/sensors/nexus-n3-sensor-movella-dot \
  --output-dir /tmp/rsnx-build-sensor
```

```bash
nexus-n3-plugin build \
  --plugin-root ./nexus-n3-plugin-catalog/algorithms/nexus-n3-algorithm-standard-loading-intensity \
  --output-dir /tmp/rsnx-build-algo
```

These produce `.rsnxplugin` bundles compatible with the Phase 1 installer in
`nexus-n3-core/nexus_n3.plugins`.

Install example:

```bash
cd /path/to/nexus-n3-core
python -m nexus_n3.plugins install /tmp/rsnx-build-sensor/nexus-n3-sensor-movella-dot-0.1.0.rsnxplugin
```

For local development driven by `config/runtime.env`, `nexus-n3-core` also
provides:

```bash
python -m nexus_n3.plugins show-dev-list
python -m nexus_n3.plugins install-dev-list
```
