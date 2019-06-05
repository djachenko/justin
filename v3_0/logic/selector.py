from abc import abstractmethod
from typing import List

from v3_0.filesystem.movable import Movable
from v3_0.models.photoset import Photoset


class Selector:
    @abstractmethod
    def source_folder(self, photoset: Photoset) -> str:
        pass

    @abstractmethod
    def select(self, photoset: Photoset) -> List[Movable]:
        pass
