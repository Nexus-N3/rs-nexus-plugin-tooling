from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def resolve_plugin_site_packages(plugin_root: Path) -> Path:
    """Return the plugin venv site-packages directory."""
    plugin_root = plugin_root.resolve()
    lib_dir = plugin_root / ".venv" / "lib"
    matches = sorted(lib_dir.glob("python*/site-packages"))

    if len(matches) != 1:
        raise FileNotFoundError(
            "Plugin site-packages directory not found.\n\n"
            f"Expected under:\n  {lib_dir}\n\n"
            "Recreate or repair the plugin environment before testing."
        )

    return matches[0]


def resolve_plugin_python(plugin_root: Path) -> Path:
    """Return the plugin-local Python executable from an existing plugin venv."""
    plugin_root = plugin_root.resolve()
    python_bin = plugin_root / ".venv" / "bin" / "python"

    if not python_bin.is_file():
        raise FileNotFoundError(
            "Plugin virtual environment not found.\n\n"
            f"Expected:\n  {python_bin}\n\n"
            "Create the plugin with:\n"
            "  nexus-n3-plugin init ...\n\n"
            "or recreate the plugin environment before testing."
        )

    return python_bin


def prepare_plugin_venv(plugin_root: Path, sdk_root: Path | None = None) -> Path:
    plugin_root = plugin_root.resolve()
    venv_dir = plugin_root / ".venv"

    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    python_bin = resolve_plugin_python(plugin_root)

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
