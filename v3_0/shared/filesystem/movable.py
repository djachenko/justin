from abc import ABC, abstractmethod

from pathlib import Path


class Movable(ABC):
    # @property
    # @abstractmethod
    # def name(self):
    #     pass

    @abstractmethod
    def move(self, path: Path):
        pass

    @abstractmethod
    def move_down(self, subfolder: str) -> None:
        pass

    @abstractmethod
    def move_up(self) -> None:
        pass

