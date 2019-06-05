from typing import Optional

from v3_0.helpers import util
from v3_0.logic.base.abstract_check import AbstractCheck
from v3_0.logic.base.extractor import Extractor
from v3_0.logic.base.selector import Selector
from v3_0.models.photoset import Photoset


class Check(AbstractCheck):
    def __init__(self, name: str, selector: Selector, hook: Optional[Extractor], message: str = "") -> None:
        super().__init__()

        assert selector is not None

        self.__selector = selector
        self.__hook = hook
        self.__name = name
        self.__message = message

    @property
    def hookable(self) -> bool:
        return self.__hook is not None

    def check(self, photoset: Photoset) -> bool:
        if self.__hook is not None:
            self.__hook.backwards(photoset)

        result = not any(self.__selector.select(photoset)) and all([self.check(part) for part in photoset.parts])

        return result

    def ask_for_extract(self):
        if self.__hook is None:
            return False

        return util.ask_for_permission(self.__message)

    def extract(self, photoset: Photoset):
        self.__hook.forward(photoset)

    def __check_inner(self, photoset: Photoset) -> bool:
        select = self.__selector.select(photoset)

        return not any(select)

    @property
    def name(self):
        return self.__name
