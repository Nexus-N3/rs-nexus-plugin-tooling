"""Base algorithm contract copied from rs-nexus-os for plugin authoring."""

from __future__ import annotations

import inspect
from pathlib import Path


class AlgorithmBase:
    """Common interface for streaming algorithm plugins."""

    def __init__(self, config):
        self.config = config
        self.result_callback = None

    @classmethod
    def algorithm_dir(cls) -> Path:
        """Return the filesystem path for the algorithm package."""
        return Path(inspect.getfile(cls)).parent

    @classmethod
    def yaml_path(cls) -> Path:
        """Return the config.yaml path for this algorithm."""
        return cls.algorithm_dir() / "config.yaml"

    def on_sample(self, sample):
        """Process an incoming sample."""
        raise NotImplementedError

    def register_result_listener(self, callback):
        """Register a callback for emitted results."""
        self.result_callback = callback

    def register_compute_delegate(self, callback):
        """Register a callback for delegated compute execution."""
        self.compute_delegate = callback

    def emit_result(self, result):
        """Emit a result via the registered callback."""
        if self.result_callback:
            self.result_callback(result)
