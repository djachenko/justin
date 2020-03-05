from datetime import timedelta
from typing import Optional

from v3_0.shared.helpers.data_size import DataSize
from v3_0.shared.helpers.data_speed import DataSpeed


class TransferTimeEstimator:
    @staticmethod
    def estimate(speed: DataSpeed, remaining_size: DataSize) -> Optional[timedelta]:
        remaining_time = remaining_size / speed

        return remaining_time
