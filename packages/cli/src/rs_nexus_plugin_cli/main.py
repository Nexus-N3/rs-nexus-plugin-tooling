"""Command line entry point for RS Nexus plugin tooling."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from rs_nexus_plugin_cli.scaffold.algorithm import scaffold_algorithm_plugin
from rs_nexus_plugin_cli.scaffold.sensor import scaffold_sensor_plugin
from rs_nexus_plugin_cli.build import build_plugin_bundle
from rs_nexus_plugin_cli.plugin_env import (
    prepare_plugin_venv,
    resolve_plugin_python,
    resolve_plugin_site_packages,
)

def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(prog="rsnexus-plugin")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Scaffold a new plugin")
    init_subparsers = init_parser.add_subparsers(dest="plugin_type", required=True)

    sensor_parser = init_subparsers.add_parser("sensor", help="Scaffold a sensor plugin")
    sensor_parser.add_argument("plugin_id", help="Plugin identifier, e.g. movella-dot")
    sensor_parser.add_argument(
        "--display-name",
        help="Human-readable sensor name",
    )
    sensor_parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where the plugin repository should be created",
    )
    sensor_parser.add_argument(
        "--adapter",
        default="BLE",
        help="Sensor adapter type to place in the generated spec",
    )
    sensor_parser.add_argument(
        "--sample-type",
        default="generic",
        help="Generated sample type identifier",
    )
    sensor_parser.add_argument(
        "--package-name",
        help="Override generated Python package name",
    )
    sensor_parser.add_argument(
        "--manufacturer-id",
        type=int,
        default=9000,
        help="Manufacturer id used in the generated SensorType",
    )
    sensor_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing empty target directory",
    )

    algorithm_parser = init_subparsers.add_parser("algorithm", help="Scaffold an algorithm plugin")
    algorithm_parser.add_argument("plugin_id", help="Plugin identifier, e.g. generic-data-summary")
    algorithm_parser.add_argument(
        "--display-name",
        help="Human-readable algorithm name",
    )
    algorithm_parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where the plugin repository should be created",
    )
    algorithm_parser.add_argument(
        "--package-name",
        help="Override generated Python package name",
    )
    algorithm_parser.add_argument(
        "--with-intermediate",
        action="store_true",
        help="Enable the intermediate schedule and generate an example implementation",
    )
    algorithm_parser.add_argument(
        "--with-consolidation",
        action="store_true",
        help="Enable the consolidation schedule and generate an example implementation",
    )
    algorithm_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing empty target directory",
    )

    build_parser = subparsers.add_parser("build", help="Build a .rsnxplugin bundle for rs-nexus-os")
    build_parser.add_argument(
        "--plugin-root",
        default=".",
        help="Plugin source repository to build",
    )
    build_parser.add_argument(
        "--output-dir",
        default="plugin-build",
        help="Directory where the .rsnxplugin bundle should be created",
    )
    build_parser.add_argument(
        "--sdk-root",
        help="Optional path to the local rs-nexus-plugin-sdk repo to include as a wheel artifact",
    )
    build_parser.add_argument(
        "--no-sdk",
        action="store_true",
        help="Do not auto-build/include the local rs-nexus-plugin-sdk wheel",
    )
    build_parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Additional wheel artifact to include in the .rsnxplugin bundle",
    )
    build_parser.add_argument(
        "--force",
        action="store_true",
        help="Deprecated compatibility flag. Existing bundles of the same name/version are overwritten automatically.",
    )

    test_parser = subparsers.add_parser("test", help="Run focused plugin development harnesses")
    test_subparsers = test_parser.add_subparsers(dest="test_type", required=True)
    sensor_test_parser = test_subparsers.add_parser("sensor", help="Run the sensor plugin harness")
    sensor_test_parser.add_argument(
        "--plugin-root",
        default=".",
        help="Sensor plugin source repository to load from source",
    )
    sensor_test_parser.add_argument("--adapter-backend", default="auto")
    sensor_test_parser.add_argument("--sensor-count", type=int, default=1)
    sensor_test_parser.add_argument("--duration", type=float, default=15.0)
    sensor_test_parser.add_argument("--identify", action="store_true")
    sensor_test_parser.add_argument("--location")
    sensor_test_parser.add_argument("--gateway-serial-port")
    sensor_test_parser.add_argument("--gateway-baudrate", type=int, default=1_000_000)
    sensor_test_parser.add_argument("--gateway-protocol-version", type=int, default=1)
    sensor_test_parser.add_argument(
        "--output-dir",
        help="Optional capture directory. Defaults to <plugin-root>/plugin-test/.",
    )
    sensor_test_parser.add_argument(
        "--attribute",
        action="append",
        default=[],
        help="Override a sensor attribute as KEY=VALUE. VALUE may be JSON.",
    )
    sensor_test_parser.add_argument("--fail-on-no-data", action="store_true")
    sensor_test_parser.add_argument(
        "--refresh-env",
        action="store_true",
        help="Reinstall the SDK and plugin into the plugin .venv before running the harness.",
    )
    bundle_test_parser = test_subparsers.add_parser("sensor-bundle", help="Run the harness against a built .rsnxplugin bundle")
    bundle_test_parser.add_argument("--bundle-path", required=True, help="Path to the built .rsnxplugin bundle")
    bundle_test_parser.add_argument(
        "--plugin-root",
        help="Optional source plugin repository. Defaults to an inferred plugin repo when using the standard dev-plugins layout.",
    )
    bundle_test_parser.add_argument("--adapter-backend", default="auto")
    bundle_test_parser.add_argument("--sensor-count", type=int, default=1)
    bundle_test_parser.add_argument("--duration", type=float, default=15.0)
    bundle_test_parser.add_argument("--identify", action="store_true")
    bundle_test_parser.add_argument("--location")
    bundle_test_parser.add_argument("--gateway-serial-port")
    bundle_test_parser.add_argument("--gateway-baudrate", type=int, default=1_000_000)
    bundle_test_parser.add_argument("--gateway-protocol-version", type=int, default=1)
    bundle_test_parser.add_argument(
        "--output-dir",
        help="Optional capture directory. Defaults to <plugin-root>/plugin-test/.",
    )
    bundle_test_parser.add_argument(
        "--attribute",
        action="append",
        default=[],
        help="Override a sensor attribute as KEY=VALUE. VALUE may be JSON.",
    )
    bundle_test_parser.add_argument("--fail-on-no-data", action="store_true")

    return parser


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init" and args.plugin_type == "sensor":
        print("Creating sensor plugin", args.plugin_id)
        plugin_root = scaffold_sensor_plugin(
            plugin_id=args.plugin_id,
            display_name=args.display_name,
            output_dir=Path(args.output_dir),
            adapter=args.adapter,
            sample_type=args.sample_type,
            package_name=args.package_name,
            manufacturer_id=args.manufacturer_id,
            force=args.force,
        )
        prepare_plugin_venv(plugin_root)
        return 0

    if args.command == "init" and args.plugin_type == "algorithm":
        print("Creating alogrithm plugin", args.plugin_id)
        plugin_root = scaffold_algorithm_plugin(
            plugin_id=args.plugin_id,
            display_name=args.display_name,
            output_dir=Path(args.output_dir),
            package_name=args.package_name,
            include_intermediate=args.with_intermediate,
            include_consolidation=args.with_consolidation,
            force=args.force,
        )
        prepare_plugin_venv(plugin_root)
        return 0

    if args.command == "build":
        build_plugin_bundle(
            plugin_root=Path(args.plugin_root),
            output_dir=Path(args.output_dir),
            force=args.force,
            sdk_root=Path(args.sdk_root) if args.sdk_root else None,
            include_sdk=not args.no_sdk,
            extra_artifacts=[Path(path) for path in args.artifact],
        )
        return 0

    if args.command == "test" and args.test_type == "sensor":
        plugin_root = Path(args.plugin_root).resolve()
        if args.refresh_env:
            prepare_plugin_venv(plugin_root)
        else:
            resolve_plugin_python(plugin_root)
        plugin_site_packages = resolve_plugin_site_packages(plugin_root)
        completed = _run_sensor_harness(
            plugin_root=plugin_root,
            plugin_site_packages=plugin_site_packages,
            adapter_backend=args.adapter_backend,
            sensor_count=args.sensor_count,
            duration=args.duration,
            identify=args.identify,
            location=args.location,
            gateway_serial_port=args.gateway_serial_port,
            gateway_baudrate=args.gateway_baudrate,
            gateway_protocol_version=args.gateway_protocol_version,
            output_dir=args.output_dir,
            attributes=args.attribute,
            fail_on_no_data=args.fail_on_no_data,
        )
        return completed.returncode

    if args.command == "test" and args.test_type == "sensor-bundle":
        bundle_path = Path(args.bundle_path).resolve()
        with tempfile.TemporaryDirectory(prefix="rsnexus-sensor-bundle-") as temp_dir:
            temp_root = Path(temp_dir)
            extracted_root = temp_root / "bundle"
            extracted_root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(bundle_path, "r") as archive:
                archive.extractall(extracted_root)

            bundle_manifest = _read_bundle_manifest(extracted_root)
            plugin_id = str(bundle_manifest["plugin_id"])
            plugin_type = str(bundle_manifest["plugin_type"])
            test_env_root = temp_root / "env"
            bundle_site_packages = _prepare_bundle_test_env(extracted_root, test_env_root)
            plugin_root = (
                Path(args.plugin_root).resolve()
                if args.plugin_root
                else _infer_bundle_plugin_root(bundle_path, plugin_id, plugin_type)
            )
            output_dir = args.output_dir or str(plugin_root / "plugin-test")
            completed = _run_sensor_harness(
                plugin_root=extracted_root,
                plugin_site_packages=bundle_site_packages,
                adapter_backend=args.adapter_backend,
                sensor_count=args.sensor_count,
                duration=args.duration,
                identify=args.identify,
                location=args.location,
                gateway_serial_port=args.gateway_serial_port,
                gateway_baudrate=args.gateway_baudrate,
                gateway_protocol_version=args.gateway_protocol_version,
                output_dir=output_dir,
                attributes=args.attribute,
                fail_on_no_data=args.fail_on_no_data,
            )
            return completed.returncode
    
    parser.error("Unsupported command")
    return 2


def _run_sensor_harness(
    *,
    plugin_root: Path,
    plugin_site_packages: Path,
    adapter_backend: str,
    sensor_count: int,
    duration: float,
    identify: bool,
    location: str | None,
    gateway_serial_port: str | None,
    gateway_baudrate: int,
    gateway_protocol_version: int,
    output_dir: str | None,
    attributes: list[str],
    fail_on_no_data: bool,
) -> subprocess.CompletedProcess:
    tooling_root = Path(__file__).resolve().parents[4]
    cli_src = tooling_root / "packages" / "cli" / "src"
    sdk_src = tooling_root / "packages" / "sdk" / "src"
    pythonpath_entries = [str(cli_src), str(sdk_src), str(plugin_site_packages)]
    existing_pythonpath = os.environ.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    cmd = [
        sys.executable,
        "-m",
        "rs_nexus_plugin_cli.sensor_harness.cli",
        "--plugin-root",
        str(plugin_root),
        "--adapter-backend",
        adapter_backend,
        "--sensor-count",
        str(sensor_count),
        "--duration",
        str(duration),
        "--gateway-baudrate",
        str(gateway_baudrate),
        "--gateway-protocol-version",
        str(gateway_protocol_version),
    ]
    if identify:
        cmd.append("--identify")
    if location:
        cmd.extend(["--location", location])
    if gateway_serial_port:
        cmd.extend(["--gateway-serial-port", gateway_serial_port])
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    for item in attributes:
        cmd.extend(["--attribute", item])
    if fail_on_no_data:
        cmd.append("--fail-on-no-data")
    return subprocess.run(cmd, check=False, env=env)


def _read_bundle_manifest(extracted_root: Path) -> dict:
    manifest_path = extracted_root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Extracted bundle missing manifest.json: {manifest_path}")
    import json
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _prepare_bundle_test_env(extracted_root: Path, env_root: Path) -> Path:
    env_root.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(env_root)], check=True)
    python_bin = env_root / "bin" / "python"
    artifacts_dir = extracted_root / "artifacts"
    wheel_paths = sorted(artifacts_dir.glob("*.whl"))
    if not wheel_paths:
        raise FileNotFoundError(f"No wheel artifacts found in {artifacts_dir}")
    subprocess.run(
        [
            str(python_bin),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(artifacts_dir),
            *[str(path) for path in wheel_paths],
        ],
        check=True,
    )
    site_packages_matches = sorted((env_root / "lib").glob("python*/site-packages"))
    if len(site_packages_matches) != 1:
        raise FileNotFoundError(f"Bundle test environment site-packages not found under {env_root / 'lib'}")
    return site_packages_matches[0]


def _infer_bundle_plugin_root(bundle_path: Path, plugin_id: str, plugin_type: str) -> Path:
    family_dir = "sensors" if plugin_type == "sensor" else "algorithms"
    repo_prefix = "rs-nexus-sensor-" if plugin_type == "sensor" else "rs-nexus-algorithm-"
    if bundle_path.parent.name == family_dir and bundle_path.parent.parent.name == "plugin-builds":
        workspace_root = bundle_path.parent.parent.parent
        candidate = workspace_root / family_dir / f"{repo_prefix}{plugin_id}"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not infer the source plugin repository from the bundle path.\n\n"
        f"Bundle path:\n  {bundle_path}\n\n"
        "Pass --plugin-root explicitly when testing a built bundle outside the standard dev-plugins layout."
    )


if __name__ == "__main__":
    raise SystemExit(main())
