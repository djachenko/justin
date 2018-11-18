from abc import abstractmethod
from typing import List, Optional

from v3_0.logic.filter import Filter
from v3_0.logic.selector import Selector
from v3_0.models.photoset import Photoset


class Check:
    def __init__(self, messages: List[str], selector: Selector, hook: Optional[Filter]) -> None:
        super().__init__()

        assert selector is not None
        assert messages is not None
        assert len(messages) == 2

        self.__selector = selector
        self.__hook = hook
        self.__messages = messages

    @property
    def hookable(self) -> bool:
        return self.__hook is not None

    def extract(self, photoset: Photoset):
        self.__hook.forward(photoset)

    def check(self, photoset: Photoset) -> bool:
        if self.__hook is not None:
            self.__hook.backwards(photoset)

        result = not any(self.__selector.select(photoset)) and all([self.check(part) for part in photoset.parts])

        return result

    def __check_inner(self, photoset: Photoset) -> bool:
        select = self.__selector.select(photoset)

        return not any(select)

    @property
    @abstractmethod
    def name(self):
        assert False

    @property
    @abstractmethod
    def failed_files_characteristic(self):
        assert False

    @property
    def file_type(self):
        return "Files"
