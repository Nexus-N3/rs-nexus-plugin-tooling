#!/usr/bin/env python3
"""Run a source-mode sensor plugin against the CLI harness."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SDK_SRC = REPO_ROOT / "packages" / "sdk" / "src"
CLI_SRC = REPO_ROOT / "packages" / "cli" / "src"
sys.path.insert(0, str(SDK_SRC))
sys.path.insert(0, str(CLI_SRC))

from nexus_n3_plugin_cli.sensor_harness.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
