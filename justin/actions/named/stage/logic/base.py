from abc import abstractmethod
from typing import Optional, List

from justin_utils import util

from justin.actions.named.stage.logic.exceptions.extractor_error import ExtractorError
from justin.shared.filesystem import PathBased, RelativeFileset
from justin.shared.helpers import photoset_utils
from justin.shared.models.photoset import Photoset


class AbstractCheck:
    @abstractmethod
    def is_good(self, photoset: Photoset) -> bool:
        pass


class Selector:
    @abstractmethod
    def select(self, photoset: Photoset) -> List[str]:
        pass


class Extractor:
    def __init__(self, name: str, selector: Selector, filter_folder: str,
                 prechecks: List[AbstractCheck] = None) -> None:
        super().__init__()

        if not prechecks:
            prechecks = []

        self.__name = name
        self.__selector = selector
        self.__filter_folder = filter_folder
        self.__prechecks = prechecks

    @property
    def selector(self) -> Selector:
        return self.__selector

    def __run_prechecks(self, photoset: Photoset) -> bool:
        return all([precheck.is_good(photoset) for precheck in self.__prechecks])

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        selection = self.__selector.select(photoset)

        files_to_move = photoset_utils.files_by_stems(selection, photoset)

        return files_to_move

    def forward(self, photoset: Photoset):
        for part in photoset.parts:
            if not self.__run_prechecks(part):
                raise ExtractorError(f"Failed prechecks while running {self.__name} extractor forward on {part.name}")

            files_to_move = self.files_to_extract(part)
            files_to_move = list(set(files_to_move))

            virtual_set = RelativeFileset(part.path, files_to_move)

            virtual_set.move_down(self.__filter_folder)

        photoset.tree.refresh()

    def backwards(self, photoset: Photoset):
        for part in photoset.parts:
            if not self.__run_prechecks(part):
                raise ExtractorError(f"Failed prechecks while running {self.__name} extractor backwards on {part.name}")

            filtered = part.tree[self.__filter_folder]

            if not filtered:
                continue

            filtered_photoset = Photoset(filtered)

            if not self.__run_prechecks(filtered_photoset):
                raise ExtractorError(f"Failed prechecks while running {self.__name} extractor backwards on {part.name}/"
                                     f"{self.__filter_folder}")

            filtered_set = RelativeFileset(filtered.path, filtered.flatten())

            filtered_set.move_up()

        photoset.tree.refresh()


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

    @property
    def name(self):
        return self.__name

    def __repr__(self) -> str:
        return self.name.capitalize()
