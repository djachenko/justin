from abc import abstractmethod
from typing import List

from justin.shared.models.photoset import Photoset


class Selector:
    @abstractmethod
    def select(self, photoset: Photoset) -> List[str]:
        pass
