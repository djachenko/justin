from abc import abstractmethod

from v3_0.shared.models.photoset import Photoset


class AbstractCheck:
    @abstractmethod
    def is_good(self, photoset: Photoset) -> bool:
        pass
