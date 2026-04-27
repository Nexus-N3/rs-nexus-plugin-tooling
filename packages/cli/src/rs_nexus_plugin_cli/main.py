"""Command line entry point for RS Nexus plugin tooling."""

from __future__ import annotations

import argparse
from pathlib import Path

from rs_nexus_plugin_cli.scaffold.algorithm import scaffold_algorithm_plugin
from rs_nexus_plugin_cli.scaffold.sensor import scaffold_sensor_plugin


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
        help="Generate an intermediate executor module",
    )
    algorithm_parser.add_argument(
        "--with-consolidation",
        action="store_true",
        help="Generate a consolidation executor module",
    )
    algorithm_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing empty target directory",
    )

    return parser


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init" and args.plugin_type == "sensor":
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

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
