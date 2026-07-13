# Getting Started

This tutorial walks through the current RS Nexus plugin development flow using
the example workspace layout:

```text
/home/mike/Desktop/apps/dev/rs-nexus-project/
  rs-nexus-plugin-tooling/
  dev-plugins/
    sensors/
    algorithms/
    plugin-builds/
      sensors/
      algorithms/
```

## 1. Clone And Install The Tooling

Clone the tooling repository into the workspace root if it is not already
present:

```bash
cd /home/mike/Desktop/apps/dev/rs-nexus-project
git clone <repo-url> rs-nexus-plugin-tooling
```

Install the tooling:

```bash
cd /home/mike/Desktop/apps/dev/rs-nexus-project/rs-nexus-plugin-tooling
./install.sh
```

This creates or reuses the tooling virtual environment:

```text
/home/mike/Desktop/apps/dev/rs-nexus-project/rs-nexus-plugin-tooling/.venv
```

It also installs a shared `rsnexus-plugin` launcher into:

```text
~/.local/bin/rsnexus-plugin
```

If `~/.local/bin` is not already on `PATH`, add it:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 2. Create The Plugin Workspace Directories

Create the workspace directories once:

```bash
mkdir -p /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors
mkdir -p /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/algorithms
mkdir -p /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/sensors
mkdir -p /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/algorithms
```

## 3. Scaffold A New Sensor Plugin

Change into the sensor workspace:

```bash
cd /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors
```

Scaffold a new sensor plugin:

```bash
rsnexus-plugin init sensor my-sensor
```

This creates:

```text
/home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor
```

It also creates the plugin-local virtual environment:

```text
/home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor/.venv
```

The plugin `.venv` is used for plugin dependencies only. The CLI is not
installed into the plugin environment.

## 4. Implement The Plugin

Work inside the generated plugin repository:

```bash
cd /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor
```

Implement the plugin in files such as:

```text
src/rs_nexus_sensor_my_sensor/sensor.py
src/rs_nexus_sensor_my_sensor/samples.py
src/rs_nexus_sensor_my_sensor/MySensorSpec.yaml
```

## 5. Run The Sensor Harness Test

Run the shared CLI from anywhere. The harness will execute against the plugin
source tree in the tooling environment, while adding the plugin `.venv`
site-packages for plugin-side dependencies.

The default `test sensor` flow does not rebuild or reinstall the plugin. It is
intended for source-mode testing before bundle creation.

At present this command is not a built-bundle validation command. The built
plugin path can also be tested locally with `rsnexus-plugin test sensor-bundle`
after building the `.rsnxplugin`.

Example using a generic sensor plugin path:

```bash
rsnexus-plugin test sensor \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor
```

If you explicitly want to refresh the plugin `.venv` before the run, add:

```bash
rsnexus-plugin test sensor \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor \
  --refresh-env
```

Example using the Movesense plugin with the gateway backend:

```bash
rsnexus-plugin test sensor \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-movesense \
  --adapter-backend nexus_ble_gateway \
  --gateway-serial-port /dev/serial/by-id/your_gateway_port \
  --duration 15 \
  --fail-on-no-data
```

Example using direct host BLE:

```bash
rsnexus-plugin test sensor \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-movesense \
  --adapter-backend bleak \
  --duration 15 \
  --fail-on-no-data
```

Useful optional flags:

- `--identify`
- `--sensor-count N`
- `--location <location>`
- `--attribute KEY=VALUE`
- `--output-dir /custom/output/path`

To test an algorithm plugin against a specific sensor plugin, use:

```bash
rsnexus-plugin test algorithm \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity \
  --sensor-plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-movesense \
  --adapter-backend nexus_ble_gateway \
  --gateway-serial-port /dev/serial/by-id/your_gateway_port \
  --duration 15 \
  --fail-on-no-results
```

This writes sensor capture CSV files and compute JSONL files under the
algorithm plugin's `plugin-test/` directory.

Those compute files follow the same stage split used by `rs-nexus-os`:

- `computed/real_time.jsonl`
- `computed/intermediate.jsonl`
- `computed/consolidated.jsonl`

The shared contract is that these are compute results with consistent `stage`
semantics. The payload body itself remains algorithm-specific.

To use the built Movesense bundle instead of the sensor source tree:

```bash
rsnexus-plugin test algorithm \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/algorithms/rs-nexus-algorithm-standard-loading-intensity \
  --sensor-bundle-path /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/sensors/rs-nexus-sensor-movesense-0.1.2.rsnxplugin \
  --adapter-backend nexus_ble_gateway \
  --gateway-serial-port /dev/serial/by-id/your_gateway_port \
  --duration 15 \
  --fail-on-no-results
```

To validate a built algorithm bundle as well:

```bash
rsnexus-plugin test algorithm-bundle \
  --bundle-path /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/algorithms/your-algorithm.rsnxplugin \
  --sensor-bundle-path /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/sensors/rs-nexus-sensor-movesense-0.1.2.rsnxplugin \
  --adapter-backend nexus_ble_gateway \
  --gateway-serial-port /dev/serial/by-id/your_gateway_port \
  --duration 15 \
  --fail-on-no-results
```

## 6. Review The Captured Output

By default the harness writes captured data under the plugin repository:

```text
/home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor/
  plugin-test/
    <sample-type>.csv
    errors.log
```

For the Movesense example this becomes:

```text
/home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-movesense/
  plugin-test/
    ecg.csv
    hr.csv
    temp.csv
    errors.log
```

These CSV files are the main developer inspection output from the test run.

## 7. Build The Plugin Bundle

Once the harness run is satisfactory, build the final plugin bundle:

```bash
rsnexus-plugin build \
  --plugin-root /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor \
  --output-dir /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/sensors
```

This produces a `.rsnxplugin` bundle for later installation into
`rs-nexus-os`.

## 8. Test The Built Plugin Bundle

You can also validate the built `.rsnxplugin` locally:

```bash
rsnexus-plugin test sensor-bundle \
  --bundle-path /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/sensors/rs-nexus-sensor-my-sensor-0.1.0.rsnxplugin \
  --adapter-backend bleak \
  --duration 15 \
  --fail-on-no-data
```

For gateway testing:

```bash
rsnexus-plugin test sensor-bundle \
  --bundle-path /home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/plugin-builds/sensors/rs-nexus-sensor-movesense-0.1.0.rsnxplugin \
  --adapter-backend nexus_ble_gateway \
  --gateway-serial-port /dev/serial/by-id/your_gateway_port \
  --duration 15 \
  --fail-on-no-data
```

By default the built-bundle harness writes capture files into the source plugin
repository, not into `plugin-builds`:

```text
/home/mike/Desktop/apps/dev/rs-nexus-project/dev-plugins/sensors/rs-nexus-sensor-my-sensor/
  plugin-test/
```
