"""CLI entry point for the source-mode algorithm harness runner."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .runner import build_harness_config, run_algorithm_test


def build_parser() -> argparse.ArgumentParser:
    """Build the parser for source-mode algorithm harness execution."""
    parser = argparse.ArgumentParser(
        description="Run a source-mode algorithm plugin against a sensor plugin via the CLI harness."
    )
    parser.add_argument("--plugin-root", type=Path, required=True, help="Algorithm plugin source repository to load from source.")
    parser.add_argument("--sensor-plugin-root", type=Path, required=True, help="Sensor plugin source repository used to feed samples into the algorithm.")
    parser.add_argument("--adapter-backend", default="auto")
    parser.add_argument("--sensor-count", type=int, default=1)
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--identify", action="store_true")
    parser.add_argument("--location")
    parser.add_argument("--gateway-serial-port")
    parser.add_argument("--gateway-baudrate", type=int, default=1_000_000)
    parser.add_argument("--gateway-protocol-version", type=int, default=1)
    parser.add_argument("--subject-id", default="harness-subject-1")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional capture directory. Defaults to <algorithm-plugin-root>/plugin-test/.",
    )
    parser.add_argument(
        "--attribute",
        action="append",
        default=[],
        help="Override a sensor attribute as KEY=VALUE. VALUE may be JSON.",
    )
    parser.add_argument(
        "--algorithm-input",
        action="append",
        default=[],
        help="Override an algorithm input parameter as KEY=VALUE. VALUE may be JSON.",
    )
    parser.add_argument("--fail-on-no-results", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and run the algorithm harness."""
    parser = build_parser()
    args = parser.parse_args(argv)
    config = build_harness_config(args)
    return asyncio.run(run_algorithm_test(config, output_dir=args.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
