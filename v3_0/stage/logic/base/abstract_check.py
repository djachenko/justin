from abc import abstractmethod

from v3_0.shared.models.photoset import Photoset


class AbstractCheck:
    @abstractmethod
    def check(self, photoset: Photoset) -> bool:
        pass
