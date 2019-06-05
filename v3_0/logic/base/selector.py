from abc import abstractmethod
from typing import List

from v3_0.models.photoset import Photoset


class Selector:
    @abstractmethod
    def select(self, photoset: Photoset) -> List[str]:
        pass
