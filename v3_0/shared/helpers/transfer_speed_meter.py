from datetime import datetime
from typing import List, Tuple

from v3_0.shared.helpers.data_size import DataSize
from v3_0.shared.helpers.data_speed import DataSpeed


class TransferSpeedMeter:
    __HISTORY_SIZE = 6

    # noinspection PyTypeChecker
    def __init__(self):
        self.__global_start_time: datetime = None
        self.__global_stop_time: datetime = None
        self.__total_size: int = None

        self.__history_start_time: datetime = None
        self.__history: List[Tuple[datetime, int]] = []

    def start(self):
        now = datetime.now()

        self.__global_start_time = now
        self.__total_size = 0

        self.__history_start_time = now
        self.__history = [(now, 0) for _ in range(TransferSpeedMeter.__HISTORY_SIZE)]

    def feed(self, size: int):
        assert len(self.__history) > 0

        now = datetime.now()

        self.__total_size += size
        self.__global_stop_time = now

        self.__history.append((now, size))
        self.__history_start_time = self.__history[0][0]

        self.__history = self.__history[-TransferSpeedMeter.__HISTORY_SIZE:]

    @property
    def current_value(self) -> DataSpeed:
        assert len(self.__history) > 0

        total_size = sum(size for _, size in self.__history)
        elapsed_time = self.__history[-1][0] - self.__history_start_time

        return DataSpeed(DataSize.from_bytes(total_size), elapsed_time)

    @property
    def average_value(self):
        return DataSpeed(DataSize.from_bytes(self.__total_size), self.__global_stop_time - self.__global_start_time)
