from abc import ABC, abstractmethod
from typing import List

from justin.shared.models.photoset import Photoset


class StemSelecting(ABC):
    @abstractmethod
    def select_stems(self, photoset: Photoset) -> List[str]:
        raise NotImplementedError
