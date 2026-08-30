from abc import ABC

from justin.shared.models.photoset import Photoset


class Hook(ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    def fix(self, photoset: Photoset) -> None:
        pass

    def unfix(self, photoset: Photoset) -> None:
        pass
