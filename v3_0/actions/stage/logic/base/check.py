from typing import Optional

from v3_0.shared.helpers import util
from v3_0.actions.stage.logic.base.abstract_check import AbstractCheck
from v3_0.actions.stage.logic.base.extractor import Extractor
from v3_0.actions.stage.logic.base.selector import Selector
from v3_0.shared.models.photoset import Photoset


class Check(AbstractCheck):
    def __init__(self, name: str, selector: Optional[Selector] = None, hook: Optional[Extractor] = None,
                 message: str = "") -> None:
        super().__init__()

        self.__selector = selector
        self.__hook = hook
        self.__name = name
        self.__message = message

    @property
    def hookable(self) -> bool:
        return self.__hook is not None

    @property
    def message(self) -> str:
        return self.__message

    def __check_part(self, photoset: Photoset) -> bool:
        return len(self.__selector.select(photoset)) == 0

    def is_good(self, photoset: Photoset) -> bool:
        result = all(self.__check_part(part) for part in photoset.parts)

        return result

    def ask_for_extract(self):
        if self.__hook is None:
            return False

        return util.ask_for_permission(self.__message)

    def extract(self, photoset: Photoset):
        if self.hookable:
            self.__hook.forward(photoset)

    def rollback(self, photoset: Photoset):
        if self.hookable:
            self.__hook.backwards(photoset)

    def __check_inner(self, photoset: Photoset) -> bool:
        select = self.__selector.select(photoset)

        return not any(select)

    @property
    def name(self):
        return self.__name

    def __repr__(self) -> str:
        return self.name.capitalize()
