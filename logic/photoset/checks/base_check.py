from abc import abstractmethod, abstractproperty
from typing import List, Optional

from logic.photoset.filters.filter import Filter
from logic.photoset.selectors.base_selector import BaseSelector
from models.photoset import Photoset


class BaseCheck:
    def __init__(self, messages: List[str], selector: BaseSelector, hook: Optional[Filter]) -> None:
        super().__init__()

        assert selector is not None
        assert messages is not None
        assert len(messages) == 2

        self.__selector = selector
        self.__hook = hook
        self.__messages = messages

    def check(self, photoset: Photoset) -> bool:
        if self.__hook is not None:
            self.__hook.backwards(photoset)

        print("Running {check_name} for {photoset_name}... ".format(
            photoset_name=photoset.name, check_name=self.check_name), end="")

        result = self.__check_inner(photoset) and all([self.check(part) for part in photoset.parts])

        if result:
            print("passed")
        else:
            print("not passed")

            not_passed_files = self.__selector.select(photoset)

            print("{filetype} {characteristic}:".format(filetype=self.file_type,
                                                        characteristic=self.failed_files_characteristic))

            failed_file_names = [file.name for file in not_passed_files]

            print(", ".join(failed_file_names))

            # for failed_file in not_passed_files:
            #     print(failed_file.name)

            if self.recommendation is not None:
                print(self.recommendation)

            if self.__hook is not None:
                self.__hook.forward(photoset)

        return result

    def __check_inner(self, photoset: Photoset) -> bool:
        select = self.__selector.select(photoset)

        return not any(select)

    @property
    @abstractmethod
    def check_name(self):
        assert False

    @property
    @abstractmethod
    def failed_files_characteristic(self):
        assert False

    @property
    def recommendation(self) -> Optional[str]:
        return None

    @property
    def file_type(self):
        return "Files"
