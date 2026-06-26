"""
HRSample
========

Typed data container representing a single heart rate sample.
"""

from dataclasses import dataclass
from typing import Optional, ClassVar, List, Any
from .base import SensorSample


@dataclass(frozen=True)
class HRSample(SensorSample):
    """
    Represents a single heart rate sample (beats per minute).
    """
    sample_type: ClassVar[str] = "hr"

    heart_rate: Optional[float]

    @classmethod
    def csv_header(cls) -> List[str]:
        return [
            "timestamp",
            "heart_rate",
        ]

    def to_csv_row(self) -> List[Any]:
        return [
            self.timestamp,
            self.heart_rate,
        ]
