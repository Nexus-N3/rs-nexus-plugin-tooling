"""Executor contracts for intermediate and consolidation algorithm stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


def build_intermediate_result(algorithm_name: str, stage, results: list[dict]) -> dict:
    """Build a normalized intermediate executor payload."""
    return {
        "algorithm_name": algorithm_name,
        "stage": stage,
        "results": results,
    }


def build_consolidated_result(algorithm_name: str, stage, results: list[dict]) -> dict:
    """Build a normalized consolidated executor payload."""
    return {
        "algorithm_name": algorithm_name,
        "stage": stage,
        "results": results,
    }


class ExecutorBase(ABC):
    """Base class for intermediate or consolidation executors."""

    def __init__(self):
        self._last_index = 0

    @abstractmethod
    def should_run(self, result_buffers: Dict[str, Any]) -> bool:
        """Return True when enough data is available to execute."""
        pass

    @abstractmethod
    def run(self, result_buffers: Dict[str, Any]) -> Optional[Any]:
        """Run the executor against buffered results."""
        pass

    @abstractmethod
    def compute(self, data: Dict[str, Any]) -> Any:
        """Compute the executor output."""
        pass
