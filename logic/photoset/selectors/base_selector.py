from abc import abstractmethod
from typing import List

from models.movable import Movable
from models.photoset import Photoset


class BaseSelector:
    @abstractmethod
    def source_folder(self, photoset: Photoset) -> str:
        pass

    @abstractmethod
    def select(self, photoset: Photoset) -> List[Movable]:
        pass
