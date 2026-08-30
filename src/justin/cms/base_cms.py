from abc import abstractmethod
from pathlib import Path


class BaseCMS:
    @property
    @abstractmethod
    def root(self) -> Path:
        pass
