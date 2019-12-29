from datetime import timedelta
from typing import Optional

from v3_0.shared.helpers.data_size import DataSize


class DataSpeed:
    def __init__(self, amount: DataSize, time: timedelta) -> None:
        super().__init__()

        assert isinstance(amount, DataSize)
        assert isinstance(time, timedelta)

        self.__amount = amount
        self.__time = time

    def __str__(self) -> str:
        return self.formatted()

    def formatted(self) -> str:
        speed = self.canonic_value()

        if speed is None:
            return "N/A"

        unit = DataSize.Unit.for_value(round(speed))

        converted_size = speed / unit.size

        result = f"{converted_size:.2f} {unit.acronym}/s"

        return result

    def canonic_value(self) -> Optional[float]:
        if self.__time.total_seconds() == 0:
            return None

        return self.__amount.canonic_value() / self.__time.total_seconds()
