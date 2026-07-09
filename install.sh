#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${RS_NEXUS_PLUGIN_TOOLING_VENV:-$SCRIPT_DIR/.venv}"
PYTHON_BIN="${PYTHON:-python3}"

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_CACHE_DIR=1

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  echo "Set PYTHON=/path/to/python3 and rerun this script." >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment: $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "Using existing virtual environment: $VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
VENV_CLI="$VENV_DIR/bin/rsnexus-plugin"

if [[ ! -x "$VENV_PYTHON" || ! -x "$VENV_PIP" ]]; then
  echo "Invalid virtual environment at: $VENV_DIR" >&2
  echo "Remove it or set RS_NEXUS_PLUGIN_TOOLING_VENV to another path, then rerun." >&2
  exit 1
fi

echo "Installing base Python build tooling"
"$VENV_PIP" install --upgrade pip "setuptools>=61.0" wheel "build>=1.2"

echo "Installing rs-nexus-plugin-sdk in editable mode"
"$VENV_PIP" install -e "$SCRIPT_DIR/packages/sdk"


echo "Installing rs-nexus-plugin-cli in editable mode"
"$VENV_PIP" install -e "$SCRIPT_DIR/packages/cli"

echo "Validating CLI"
"$VENV_CLI" --help >/dev/null

cat <<EOF

RS Nexus plugin tooling is installed.

Use it in this shell with:
  source "$VENV_DIR/bin/activate"

Or call it directly:
  "$VENV_CLI" init sensor my-sensor-plugin
  "$VENV_CLI" init algorithm my-algorithm-plugin

To make rsnexus-plugin available without activating the venv, add this to PATH:
  export PATH="$VENV_DIR/bin:\$PATH"

If you prefer a shared plugin-development environment instead, install:
  pip install -e "$SCRIPT_DIR/packages/sdk"
  pip install -e "$SCRIPT_DIR/packages/cli"
EOF
