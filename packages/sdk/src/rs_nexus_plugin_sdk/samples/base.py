"""Base sample model copied from rs-nexus-os for plugin authoring."""

from dataclasses import dataclass
from typing import Any, ClassVar, List, Optional


@dataclass(frozen=True)
class SensorSample:
    """Base class for sensor-emitted samples."""

    timestamp: int
    sensor_type: str
    address: str
    location: Optional[str]
    sampling_rate: Optional[int]

    sample_type: ClassVar[str]

    @classmethod
    def csv_header(cls) -> List[str]:
        raise NotImplementedError

    def to_csv_row(self) -> List[Any]:
        raise NotImplementedError
