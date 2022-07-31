from abc import abstractmethod
from typing import Optional, List, Iterable

from justin.shared.filesystem import PathBased, RelativeFileset, File
from justin.shared.helpers import photoset_utils
from justin.shared.models.photoset import Photoset
from justin_utils import util
from justin_utils.util import flatten

Problem = str


class AbstractCheck:
    @abstractmethod
    def get_problems(self, photoset: Photoset) -> Iterable[Problem]:
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

    def __run_prechecks(self, photoset: Photoset) -> Iterable[Problem]:
        return flatten(precheck.get_problems(photoset) for precheck in self.__prechecks)

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        selection = self.__selector.select(photoset)

        files_to_move = photoset_utils.files_by_stems(selection, photoset)

        return files_to_move

    def forward(self, photoset: Photoset) -> Iterable[Problem]:
        prechecks_result = self.__run_prechecks(photoset)

        if prechecks_result:
            return prechecks_result

        files_to_move = self.files_to_extract(photoset)
        files_to_move = list(set(files_to_move))

        virtual_set = RelativeFileset(photoset.path, files_to_move)

        virtual_set.move_down(self.__filter_folder)

        photoset.tree.refresh()

        return []

    def backwards(self, photoset: Photoset) -> Iterable[Problem]:
        prechecks_result = self.__run_prechecks(photoset)

        if prechecks_result:
            return prechecks_result

        filtered = photoset.tree[self.__filter_folder]

        if not filtered:
            return []

        filtered_photoset = Photoset(filtered)

        prechecks_result = self.__run_prechecks(filtered_photoset)

        if prechecks_result:
            return prechecks_result

        metafiles = [File(path) for path in filtered.collect_metafile_paths() if path.exists()]

        filtered_set = RelativeFileset(filtered.path, filtered.flatten() + metafiles)

        filtered_set.move_up()

        photoset.tree.refresh()

        return []


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

    def get_problems(self, photoset: Photoset) -> Iterable[Problem]:
        problems = []

        for part in photoset.parts:
            selection = self.__selector.select(part)

            problems += selection

        return problems

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


class MetaCheck(Check):
    def __init__(self, name: str, inner_checks: Iterable[Check]) -> None:
        super().__init__(name)

        self.__inner = inner_checks

    def get_problems(self, photoset: Photoset) -> Iterable[Problem]:
        return flatten(inner_check.get_problems(photoset) for inner_check in self.__inner)


