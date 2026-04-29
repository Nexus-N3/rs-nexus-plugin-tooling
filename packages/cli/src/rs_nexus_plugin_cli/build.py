# rs_nexus_plugin_cli/build.py

from __future__ import annotations

import shutil
import subprocess
import sys
import json
from pathlib import Path

def _load_plugin_manifest(plugin_root: Path) -> dict:
    manifest_path = plugin_root / "plugin.json"

    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Not a plugin source repo: missing plugin.json in {plugin_root}"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    required = ["plugin_id", "plugin_type", "package_name", "python_package", "entry_point"]
    missing = [key for key in required if key not in manifest]

    if missing:
        raise ValueError(f"Invalid plugin.json; missing fields: {', '.join(missing)}")

    return manifest

def build_plugin_bundle(
    plugin_root: Path,
    output_dir: Path,
    force: bool = False,
) -> Path:
    """Build an installable plugin bundle from a plugin source repo."""
    plugin_root = plugin_root.resolve()
    output_dir = output_dir.resolve()

    manifest = _load_plugin_manifest(plugin_root)

    bundle_dir = output_dir / manifest["package_name"]

    if bundle_dir.exists():
        if not force:
            raise FileExistsError(f"Bundle already exists: {bundle_dir}")
        shutil.rmtree(bundle_dir)

    # delete previous build artifacts if they exist, to ensure a clean build
    source_dist = plugin_root / "dist"
    if source_dist.exists():
        shutil.rmtree(source_dist)

    subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        cwd=plugin_root,
        check=True,
    )

    wheels = sorted((plugin_root / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError(f"Expected exactly one wheel in {plugin_root / 'dist'}, found {len(wheels)}")

    bundle_dist = bundle_dir / "dist"
    bundle_dist.mkdir(parents=True, exist_ok=False)

    shutil.copy2(plugin_root / "plugin.json", bundle_dir / "plugin.json")
    shutil.copy2(wheels[0], bundle_dist / wheels[0].name)

    if (bundle_dir / ".venv").exists():
        raise ValueError("Build bundle must not include .venv")

    return bundle_dir