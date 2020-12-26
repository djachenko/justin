from abc import abstractmethod

from justin.shared.models.photoset import Photoset


class AbstractCheck:
    @abstractmethod
    def is_good(self, photoset: Photoset) -> bool:
        pass
