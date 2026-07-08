"""Command line entry point for RS Nexus plugin tooling."""

from __future__ import annotations

import argparse
from pathlib import Path

from rs_nexus_plugin_cli.scaffold.algorithm import scaffold_algorithm_plugin
from rs_nexus_plugin_cli.scaffold.sensor import scaffold_sensor_plugin
from rs_nexus_plugin_cli.build import build_plugin_bundle

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
        default="build",
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
        help="Overwrite an existing build bundle",
    )

    test_parser = subparsers.add_parser("test", help="Run focused plugin development harnesses")
    test_subparsers = test_parser.add_subparsers(dest="test_type", required=True)
    sensor_test_parser = test_subparsers.add_parser("sensor", help="Run the sensor plugin harness")
    sensor_test_parser.add_argument(
        "--plugin-root",
        default=".",
        help="Sensor plugin source repository to load from source",
    )

    return parser


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init" and args.plugin_type == "sensor":
        print("Creating sensor plugin", args.plugin_id)
        scaffold_sensor_plugin(
            plugin_id=args.plugin_id,
            display_name=args.display_name,
            output_dir=Path(args.output_dir),
            adapter=args.adapter,
            sample_type=args.sample_type,
            package_name=args.package_name,
            manufacturer_id=args.manufacturer_id,
            force=args.force,
        )
        return 0

    if args.command == "init" and args.plugin_type == "algorithm":
        print("Creating alogrithm plugin", args.plugin_id)
        scaffold_algorithm_plugin(
            plugin_id=args.plugin_id,
            display_name=args.display_name,
            output_dir=Path(args.output_dir),
            package_name=args.package_name,
            include_intermediate=args.with_intermediate,
            include_consolidation=args.with_consolidation,
            force=args.force,
        )
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
        from rs_nexus_plugin_cli.harness import run_sensor_harness
        run_sensor_harness(
            plugin_root=Path(args.plugin_root),
        )
        return 0
    
    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
