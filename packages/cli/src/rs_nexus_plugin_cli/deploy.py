"""Local deployment helpers for plugin development."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def _load_plugin_manifest(plugin_root: Path) -> dict:
    manifest_path = plugin_root / "plugin.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Not a plugin source repo: missing plugin.json in {plugin_root}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def deploy_plugin_local(
    plugin_root: Path,
    target_python: Path,
    *,
    editable: bool = False,
    force: bool = False,
    no_deps: bool = False,
    no_build_isolation: bool = False,
) -> Path:
    """Install a plugin into a target Python runtime for local rs-nexus-os use."""
    plugin_root = plugin_root.resolve()
    target_python = target_python.resolve()

    if not plugin_root.is_dir():
        raise FileNotFoundError(f"Plugin root does not exist: {plugin_root}")
    if not target_python.is_file():
        raise FileNotFoundError(f"Target python does not exist: {target_python}")

    manifest = _load_plugin_manifest(plugin_root)
    dist_name = manifest.get("package_name") or plugin_root.name

    install_args = [str(target_python), "-m", "pip", "install"]
    if force:
        install_args.extend(["--force-reinstall", "--upgrade"])
    if no_deps:
        install_args.append("--no-deps")
    if no_build_isolation:
        install_args.append("--no-build-isolation")

    if editable:
        install_target = plugin_root
        install_args.extend(["-e", str(install_target)])
    else:
        dist_dir = plugin_root / "dist"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel"],
            cwd=plugin_root,
            check=True,
        )
        wheels = sorted(dist_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError(f"Expected exactly one wheel in {dist_dir}, found {len(wheels)}")
        install_target = wheels[0]
        install_args.append(str(install_target))

    subprocess.run(install_args, check=True)

    print(f"Installed {dist_name} into {target_python}")
    print("Current rs-nexus-os picks up plugins from Python entry points in the target environment.")
    print("SDK-migrated plugins still need the rs-nexus-os runtime refactor before the current core can instantiate them.")
    return install_target
