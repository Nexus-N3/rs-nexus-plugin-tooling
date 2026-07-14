"""Bundle installation helpers for rs-nexus-os plugin catalogs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path


def install_bundle(*, bundle_path: Path, activate: bool = True) -> int:
    """Install a built plugin bundle through the rs-nexus-os installer."""
    bundle_path = bundle_path.resolve()

    ## checks
    if not bundle_path.is_file():
        raise FileNotFoundError(f"Bundle not found: {bundle_path}")
    if bundle_path.suffix != ".rsnxplugin":
        raise ValueError(f"Expected a .rsnxplugin bundle: {bundle_path}")

    ## read the bundles manifest (json) from the bundle which is jsut a zip file
    manifest = _read_bundle_manifest(bundle_path)
    print("Installing plugin bundle")
    print(f"  plugin_id: {manifest.get('plugin_id')}")
    print(f"  plugin_type: {manifest.get('plugin_type')}")
    print(f"  display_name: {manifest.get('display_name')}")
    print(f"  version: {manifest.get('version')}")
    print(f"  bundle_path: {bundle_path}")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(_pythonpath_entries(env))
    # excute the install file in rs-nexus-os/rs_nexus_plugins 
    cmd = [sys.executable, "-m", "rs_nexus_plugins", "install", str(bundle_path)]

    # if the user does not want to activate the plugin...really there should be no need for this
    # and they should always be active
    if not activate:
        cmd.append("--no-activate")
    completed = subprocess.run(cmd, check=False, env=env)
    return completed.returncode


def _read_bundle_manifest(bundle_path: Path) -> dict:
    with zipfile.ZipFile(bundle_path, "r") as archive:
        return json.loads(archive.read("manifest.json").decode("utf-8"))


def _pythonpath_entries(env: dict[str, str]) -> list[str]:
    tooling_root = Path(__file__).resolve().parents[4]
    # assumes the tooling is in the same directory as rs-nexus-os system
    # meaning alongside each other.
    rs_nexus_os_root = tooling_root.parent / "rs-nexus-os"
    entries = [str(rs_nexus_os_root)]
    existing = env.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    return entries
