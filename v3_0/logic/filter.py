from abc import abstractmethod

from v3_0.models.photoset import Photoset


class Filter:
    @abstractmethod
    def forward(self, photoset: Photoset) -> None:
        pass

    @abstractmethod
    def backwards(self, photoset: Photoset) -> None:
        pass
