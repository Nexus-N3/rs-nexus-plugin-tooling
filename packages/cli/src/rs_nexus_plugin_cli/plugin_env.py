from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def prepare_plugin_venv(plugin_root: Path, sdk_root: Path | None = None) -> Path:
    plugin_root = plugin_root.resolve()
    venv_dir = plugin_root / ".venv"

    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    python_bin = venv_dir / "bin" / "python"

    if not python_bin.exists():
        raise RuntimeError(f"Plugin venv is invalid: {venv_dir}")

    subprocess.run(
        [
            str(python_bin),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools>=61.0",
            "wheel",
            "build>=1.2",
        ],
        check=True,
    )

    resolved_sdk_root = sdk_root or _default_sdk_root()

    if resolved_sdk_root is not None:
        subprocess.run(
            [str(python_bin), "-m", "pip", "install", "-e", str(resolved_sdk_root)],
            check=True,
        )

    subprocess.run(
        [str(python_bin), "-m", "pip", "install", "-e", str(plugin_root)],
        check=True,
    )

    return python_bin


def _default_sdk_root() -> Path | None:
    candidate = Path(__file__).resolve().parents[4] / "packages" / "sdk"
    if candidate.joinpath("setup.py").is_file():
        return candidate
    return None