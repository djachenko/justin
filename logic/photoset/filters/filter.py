from abc import abstractmethod

from models.photoset import Photoset


class Filter:
    @abstractmethod
    def forward(self, photoset: Photoset) -> None:
        pass

    @abstractmethod
    def backwards(self, photoset: Photoset) -> None:
        pass
