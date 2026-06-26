"""ECG sample model copied from rs-nexus-os for plugin authoring."""

from dataclasses import dataclass
from typing import Any, ClassVar, List, Optional

from .base import SensorSample


@dataclass(frozen=True)
class ECGSample(SensorSample):
    """Represents a single ECG voltage sample."""

    sample_type: ClassVar[str] = "ecg"

    voltage: Optional[float]

    @classmethod
    def csv_header(cls) -> List[str]:
        return [
            "timestamp",
            "voltage",
        ]

    def to_csv_row(self) -> List[Any]:
        return [
            self.timestamp,
            self.voltage,
        ]
