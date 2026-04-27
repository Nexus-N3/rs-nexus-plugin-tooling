"""IMU sample model copied from rs-nexus-os for plugin authoring."""

from dataclasses import dataclass
from typing import Any, ClassVar, List, Optional, Tuple

from .base import SensorSample


@dataclass(frozen=True)
class IMUSample(SensorSample):
    """Represents a single timestamped IMU sample."""

    sample_type: ClassVar[str] = "imu"

    quat: Optional[Tuple[float, float, float, float]]
    accel: Optional[Tuple[float, float, float]]
    gyro: Optional[Tuple[float, float, float]]

    @classmethod
    def csv_header(cls) -> List[str]:
        return [
            "timestamp",
            "q_w",
            "q_x",
            "q_y",
            "q_z",
            "acc_x",
            "acc_y",
            "acc_z",
            "gyr_x",
            "gyr_y",
            "gyr_z",
        ]

    def to_csv_row(self) -> List[Any]:
        return [
            self.timestamp,
            *(self.quat or (None, None, None, None)),
            *(self.accel or (None, None, None)),
            *(self.gyro or (None, None, None)),
        ]
