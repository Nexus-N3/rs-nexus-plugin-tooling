"""CLI entry point for the SDK sensor harness runner."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .runner import build_harness_config, run_sensor_test


def build_parser() -> argparse.ArgumentParser:
    """Build the parser for source-mode sensor harness execution."""
    parser = argparse.ArgumentParser(description="Run a source-mode sensor plugin against the CLI harness.")
    parser.add_argument("--plugin-root", required=True, type=Path)
    parser.add_argument("--adapter-backend", default="auto")
    parser.add_argument("--sensor-count", type=int, default=1)
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--identify", action="store_true")
    parser.add_argument("--location")
    parser.add_argument("--gateway-serial-port")
    parser.add_argument("--gateway-baudrate", type=int, default=1_000_000)
    parser.add_argument("--gateway-protocol-version", type=int, default=1)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional capture directory. Defaults to <plugin-root>/plugin-test/.",
    )
    parser.add_argument(
        "--attribute",
        action="append",
        default=[],
        help="Override a sensor attribute as KEY=VALUE. VALUE may be JSON.",
    )
    parser.add_argument("--fail-on-no-data", action="store_true")
    return parser


def main() -> int:
    """Parse CLI arguments and run the generic sensor harness."""
    args = build_parser().parse_args()
    config = build_harness_config(args)
    try:
        return asyncio.run(run_sensor_test(config, output_dir=args.output_dir))
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
