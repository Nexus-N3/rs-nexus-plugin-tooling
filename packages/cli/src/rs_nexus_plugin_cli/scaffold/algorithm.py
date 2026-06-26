"""Algorithm plugin scaffolding helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AlgorithmPluginTemplate:
    """Normalized metadata used to render an algorithm plugin scaffold."""

    plugin_id: str
    repo_name: str
    package_name: str
    class_name: str
    result_class_name: str
    display_name: str
    algorithm_name: str
    include_intermediate: bool
    include_consolidation: bool


def scaffold_algorithm_plugin(
    plugin_id: str,
    display_name: str | None,
    output_dir: Path,
    package_name: str | None,
    include_intermediate: bool,
    include_consolidation: bool,
    force: bool,
) -> Path:
    """Create a new standalone algorithm plugin repository."""
    output_dir = _resolve_output_dir(output_dir, "algorithms")
    normalized_id = _normalize_plugin_id(plugin_id)
    template = _build_template(
        plugin_id=normalized_id,
        display_name=display_name,
        package_name=package_name,
        include_intermediate=include_intermediate,
        include_consolidation=include_consolidation,
    )
    target_dir = output_dir / template.repo_name
    _prepare_target_dir(target_dir, force=force)

    _write_text(target_dir / "README.md", _render_readme(template))
    _write_text(target_dir / "pyproject.toml", _render_pyproject(template))
    plugin_manifest = _render_plugin_manifest(template)
    _write_text(target_dir / "plugin.json", plugin_manifest)

    package_root = target_dir / "src" / template.package_name
    _write_text(package_root / "__init__.py", _render_package_init(template))
    _write_text(package_root / "plugin.json", plugin_manifest)
    _write_text(package_root / "config.yaml", _render_config(template))
    _write_text(package_root / "core.py", _render_core(template))
    _write_text(package_root / "core_schema.py", _render_core_schema(template))
    _write_text(package_root / "processing.py", _render_processing(template))
    _write_text(package_root / "intermediate_executor.py", _render_intermediate_executor(template))
    _write_text(package_root / "consolidation_executor.py", _render_consolidation_executor(template))

    tests_root = target_dir / "tests"
    _write_text(tests_root / "test_import.py", _render_test_import(template))
    _write_text(tests_root / "test_config.py", _render_test_config(template))
    _write_text(tests_root / "test_manifest.py", _render_test_manifest(template))
    _write_text(
        target_dir / ".gitignore",
        ".venv/\n__pycache__/\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n",
    )
    return target_dir


def _normalize_plugin_id(plugin_id: str) -> str:
    value = plugin_id.strip().lower().replace("_", "-").replace(" ", "-")
    while "--" in value:
        value = value.replace("--", "-")
    if not value:
        raise ValueError("plugin_id must not be empty")
    return value


def _build_template(
    plugin_id: str,
    display_name: str | None,
    package_name: str | None,
    include_intermediate: bool,
    include_consolidation: bool,
) -> AlgorithmPluginTemplate:
    repo_name = f"rs-nexus-algorithm-{plugin_id}"
    package = package_name or plugin_id.replace("-", "_")
    display = display_name or " ".join(part.capitalize() for part in plugin_id.split("-"))
    base_name = "".join(part.capitalize() for part in plugin_id.split("-"))
    class_name = base_name if base_name.endswith("Algorithm") else base_name + "Algorithm"
    result_class_name = base_name if base_name.endswith("Result") else base_name + "Result"

    return AlgorithmPluginTemplate(
        plugin_id=plugin_id,
        repo_name=repo_name,
        package_name=package,
        class_name=class_name,
        result_class_name=result_class_name,
        display_name=display,
        algorithm_name=plugin_id.replace("-", "_"),
        include_intermediate=include_intermediate,
        include_consolidation=include_consolidation,
    )


def _prepare_target_dir(target_dir: Path, force: bool) -> None:
    if target_dir.exists():
        if any(target_dir.iterdir()):
            raise FileExistsError(f"Target directory already exists and is not empty: {target_dir}")
        if not force:
            raise FileExistsError(
                f"Target directory already exists: {target_dir}. Use --force only for an empty directory."
            )
    else:
        target_dir.mkdir(parents=True, exist_ok=False)


def _resolve_output_dir(output_dir: Path, plugin_family: str) -> Path:
    """Place plugins under a grouped dev workspace when targeting dev-plugins."""
    if output_dir.name == "dev-plugins":
        return output_dir / plugin_family
    return output_dir


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_readme(template: AlgorithmPluginTemplate) -> str:
    intermediate_status = "enabled" if template.include_intermediate else "disabled"
    consolidation_status = "enabled" if template.include_consolidation else "disabled"
    return f"""# {template.display_name} Algorithm Plugin

Standalone RS Nexus algorithm plugin for `{template.algorithm_name}`.

## Development

Install the SDK and CLI from the local tooling repo, then build this plugin:

```bash
python -m build
```

## Notes

- Generated by `rsnexus-plugin init algorithm`
- Depends on `rs-nexus-plugin-sdk`
- Intermediate schedule: {intermediate_status}
- Consolidation schedule: {consolidation_status}
- Executor files are scaffolded for every algorithm. Runtime capability is declared by `plugin.json` and `config.yaml`.
"""


def _render_pyproject(template: AlgorithmPluginTemplate) -> str:
    entry_name = template.plugin_id.replace("-", "_")
    return f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{template.repo_name}"
version = "0.1.0"
description = "{template.display_name} algorithm plugin for RS Nexus OS"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "rs-nexus-plugin-sdk>=0.1.0",
]

[project.entry-points."rs_nexus.algorithms"]
{entry_name} = "{template.package_name}.core:{template.class_name}"

[tool.setuptools]
package-dir = {{"" = "src"}}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
{template.package_name} = ["*.yaml", "plugin.json"]
"""


def _render_plugin_manifest(template: AlgorithmPluginTemplate) -> str:
    manifest = {
        "plugin_id": template.plugin_id,
        "plugin_type": "algorithm",
        "display_name": template.display_name,
        "version": "0.1.0",
        "package_name": template.repo_name,
        "python_package": template.package_name,
        "entry_point": f"{template.package_name}.core:{template.class_name}",
        "executor_entry_points": {
            "intermediate": (
                f"{template.package_name}.intermediate_executor:"
                f"{template.class_name.removesuffix('Algorithm')}IntermediateExecutor"
            ),
            "consolidation": (
                f"{template.package_name}.consolidation_executor:"
                f"{template.class_name.removesuffix('Algorithm')}ConsolidationExecutor"
            ),
        },
        "config_path": f"{template.package_name}/config.yaml",
        "sdk_version": "0.1.0",
        "min_rs_nexus_os_version": "0.0.0",
        "algorithm_name": template.algorithm_name,
        "supports_intermediate": template.include_intermediate,
        "supports_consolidation": template.include_consolidation,
    }
    return json.dumps(manifest, indent=2) + "\n"


def _render_package_init(template: AlgorithmPluginTemplate) -> str:
    return f'''"""Package for the {template.display_name} algorithm plugin."""\n\nfrom .core import {template.class_name}\n\n__all__ = ["{template.class_name}"]\n'''


def _render_config(template: AlgorithmPluginTemplate) -> str:
    return f'''algorithm:
  name: {template.algorithm_name}
  version: 1.0
  description: >
    Generated algorithm plugin scaffold.
  compute:
    delegate: true

inputs:
  sensors:
    data_type: any
  parameters: {{}}

standards:
  window_seconds: 5

schedules:
  real_time:
    enabled: true
    trigger: window_complete
    emit_on_every_window: true
  intermediate:
    enabled: {str(template.include_intermediate).lower()}
    period_seconds: 30
  consolidated:
    enabled: {str(template.include_consolidation).lower()}
    trigger: stop_event
'''


def _render_core(template: AlgorithmPluginTemplate) -> str:
    return f'''"""Core algorithm implementation for {template.display_name}."""\n\nfrom rs_nexus_plugin_sdk import AlgorithmBase\nfrom rs_nexus_plugin_sdk.yaml_loader import load_yaml\n\nfrom .core_schema import ComputeStage, {template.result_class_name}\nfrom .processing import summarize_window\n\n\nclass {template.class_name}(AlgorithmBase):\n    """Generated streaming algorithm skeleton."""\n\n    name = "{template.algorithm_name}"\n\n    def __init__(self, address, sampling_rate, input_parameters=None):\n        config = load_yaml(self.yaml_path())\n        super().__init__(config)\n        self.address = address\n        self.sampling_rate = sampling_rate\n        self.subject_id = None\n        self.location = None\n        self.input_parameters = input_parameters or {{}}\n        self.buffer = []\n        self.result_count = 0\n        self.window_seconds = config["standards"]["window_seconds"]\n        self.window_size = int(self.window_seconds * sampling_rate)\n\n    def on_sample(self, sample):\n        self.buffer.append(sample)\n        if len(self.buffer) >= self.window_size:\n            delegate_cfg = self.config.get("algorithm", {{}}).get("compute", {{}})\n            delegate_enabled = delegate_cfg.get("delegate", True)\n            if delegate_enabled and getattr(self, "compute_delegate", None):\n                delegated = self.compute_delegate(self, list(self.buffer))\n                if delegated:\n                    self.buffer.clear()\n                    return\n            result = self.execute_real_time()\n            self.buffer.clear()\n            self.emit_result(result)\n\n    def execute_real_time(self):\n        self.result_count += 1\n        metrics = summarize_window(self.buffer)\n        return {template.result_class_name}(\n            address=self.address,\n            stage=ComputeStage.REAL_TIME,\n            result_count=self.result_count,\n            metrics=metrics,\n            algorithm_name=self.name,\n            subject_id=self.subject_id,\n            location=self.location,\n        )\n'''


def _render_core_schema(template: AlgorithmPluginTemplate) -> str:
    return f'''"""Schema objects for {template.display_name} results."""\n\nfrom dataclasses import dataclass\nfrom enum import Enum\nfrom typing import Any, Dict\n\n\nclass ComputeStage(str, Enum):\n    REAL_TIME = "real_time"\n    INTERMEDIATE_TIME = "intermediate_time"\n    CONSOLIDATED_TIME = "consolidated_time"\n\n\n@dataclass\nclass {template.result_class_name}:\n    address: str\n    stage: ComputeStage\n    result_count: int\n    metrics: Dict[str, Any]\n    algorithm_name: str\n    subject_id: str | None = None\n    location: str | None = None\n'''


def _render_processing(template: AlgorithmPluginTemplate) -> str:
    return '''"""Processing helpers for the generated algorithm."""\n\nfrom __future__ import annotations\n\n\ndef summarize_window(samples):\n    """Return basic metadata for the current sample window."""\n    return {\n        "sample_count": len(samples),\n        "sample_type": getattr(samples[0], "sample_type", None) if samples else None,\n    }\n'''


def _render_intermediate_executor(template: AlgorithmPluginTemplate) -> str:
    if not template.include_intermediate:
        return f'''"""Intermediate executor scaffold for {template.display_name}.\n\nThis stage is disabled in config.yaml and plugin.json until implemented.\n"""\n\nfrom rs_nexus_plugin_sdk import ExecutorBase\n\n\nclass {template.class_name.removesuffix("Algorithm")}IntermediateExecutor(ExecutorBase):\n    """Disabled intermediate executor placeholder."""\n\n    enabled = False\n\n    def should_run(self, result_buffers):\n        return False\n\n    def run(self, result_buffers):\n        return None\n\n    def compute(self, data):\n        return None\n'''

    return f'''"""Intermediate executor for {template.display_name}."""\n\nfrom rs_nexus_plugin_sdk import ExecutorBase, build_intermediate_result\n\nfrom .core_schema import ComputeStage\n\n\nclass {template.class_name.removesuffix("Algorithm")}IntermediateExecutor(ExecutorBase):\n    """Generated intermediate executor skeleton."""\n\n    def should_run(self, result_buffers):\n        return all(len(buffer) - self._last_index >= 1 for buffer in result_buffers.values())\n\n    def run(self, result_buffers):\n        data = {{address: [list(buffer)[self._last_index]] for address, buffer in result_buffers.items()}}\n        self._last_index += 1\n        return self.compute(data)\n\n    def compute(self, data):\n        results = []\n        for address, items in data.items():\n            if not items:\n                continue\n            result = items[0]\n            results.append({{"address": address, "data": getattr(result, "metrics", {{}})}})\n        return build_intermediate_result(\n            algorithm_name="{template.algorithm_name}",\n            stage=ComputeStage.INTERMEDIATE_TIME,\n            results=results,\n        )\n'''


def _render_consolidation_executor(template: AlgorithmPluginTemplate) -> str:
    if not template.include_consolidation:
        return f'''"""Consolidation executor scaffold for {template.display_name}.\n\nThis stage is disabled in config.yaml and plugin.json until implemented.\n"""\n\nfrom rs_nexus_plugin_sdk import ExecutorBase\n\n\nclass {template.class_name.removesuffix("Algorithm")}ConsolidationExecutor(ExecutorBase):\n    """Disabled consolidation executor placeholder."""\n\n    enabled = False\n\n    def should_run(self, result_buffers):\n        return False\n\n    def run(self, result_buffers):\n        return None\n\n    def compute(self, data):\n        return None\n\n    def consolidate(self, subject_id: str, intermediate_records: list[dict]) -> dict | None:\n        return None\n'''

    return f'''"""Consolidation executor for {template.display_name}."""\n\nfrom rs_nexus_plugin_sdk import ExecutorBase, build_consolidated_result\n\nfrom .core_schema import ComputeStage\n\n\nclass {template.class_name.removesuffix("Algorithm")}ConsolidationExecutor(ExecutorBase):\n    """Generated consolidation executor skeleton."""\n\n    def should_run(self, result_buffers):\n        return bool(result_buffers)\n\n    def run(self, result_buffers):\n        return None\n\n    def compute(self, data):\n        return data\n\n    def consolidate(self, subject_id: str, intermediate_records: list[dict]) -> dict:\n        payload = build_consolidated_result(\n            algorithm_name="{template.algorithm_name}",\n            stage=ComputeStage.CONSOLIDATED_TIME,\n            results=intermediate_records,\n        )\n        payload["subject_id"] = subject_id\n        return payload\n'''


def _render_test_import(template: AlgorithmPluginTemplate) -> str:
    imports = [
        f"from {template.package_name}.core import {template.class_name}",
        f"from {template.package_name}.intermediate_executor import {template.class_name.removesuffix('Algorithm')}IntermediateExecutor",
        f"from {template.package_name}.consolidation_executor import {template.class_name.removesuffix('Algorithm')}ConsolidationExecutor",
        "from rs_nexus_plugin_sdk import AlgorithmBase",
        "from rs_nexus_plugin_sdk import ExecutorBase",
    ]
    assertions = [
        f"    assert issubclass({template.class_name}, AlgorithmBase)",
        f"    assert issubclass({template.class_name.removesuffix('Algorithm')}IntermediateExecutor, ExecutorBase)",
        f"    assert issubclass({template.class_name.removesuffix('Algorithm')}ConsolidationExecutor, ExecutorBase)",
    ]

    return "\n".join(imports) + "\n\n\ndef test_generated_classes_match_sdk_contracts() -> None:\n" + "\n".join(assertions) + "\n"


def _render_test_config(template: AlgorithmPluginTemplate) -> str:
    return f'''from {template.package_name}.core import {template.class_name}\n\n\ndef test_algorithm_config_loads() -> None:\n    config = {template.class_name}.__mro__[0].yaml_path()\n    assert config.name == "config.yaml"\n'''


def _render_test_manifest(template: AlgorithmPluginTemplate) -> str:
    return f'''import json\nfrom pathlib import Path\n\n\ndef test_plugin_manifest_exists() -> None:\n    plugin_root = Path(__file__).resolve().parents[1]\n    root_manifest = json.loads((plugin_root / "plugin.json").read_text(encoding="utf-8"))\n    packaged_manifest = json.loads((plugin_root / "src" / "{template.package_name}" / "plugin.json").read_text(encoding="utf-8"))\n    assert packaged_manifest == root_manifest\n    assert root_manifest["plugin_type"] == "algorithm"\n    assert root_manifest["algorithm_name"] == "{template.algorithm_name}"\n    assert root_manifest["entry_point"] == "{template.package_name}.core:{template.class_name}"\n    assert root_manifest["executor_entry_points"]["intermediate"].endswith("IntermediateExecutor")\n    assert root_manifest["executor_entry_points"]["consolidation"].endswith("ConsolidationExecutor")\n'''
