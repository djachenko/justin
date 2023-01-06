from abc import abstractmethod, ABC
from typing import Optional, List, Iterable

from justin.shared.filesystem import PathBased, RelativeFileset, File, Folder
from justin.shared.helpers import photoset_utils
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.models.photoset import Photoset
from justin_utils import util
from justin_utils.util import flat_map, first

Problem = str


class AbstractCheck:
    @abstractmethod
    def get_problems(self, photoset: Photoset) -> Iterable[Problem]:
        pass


class Selector:
    @abstractmethod
    def select(self, photoset: Photoset) -> List[Problem]:
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
        return flat_map(precheck.get_problems(photoset) for precheck in self.__prechecks)

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

        photoset.folder.refresh()

        return []

    def backwards(self, photoset: Photoset) -> Iterable[Problem]:
        prechecks_result = self.__run_prechecks(photoset)

        if prechecks_result:
            return prechecks_result

        filtered = photoset.folder[self.__filter_folder]

        if not filtered:
            return []

        filtered_photoset = Photoset.from_folder(filtered, without_migration=True)

        prechecks_result = self.__run_prechecks(filtered_photoset)

        if prechecks_result:
            return prechecks_result

        metafiles = [File(path) for path in filtered.collect_metafile_paths() if path.exists()]

        filtered_set = RelativeFileset(filtered.path, filtered.flatten() + metafiles)

        filtered_set.move_up()

        photoset.folder.refresh()

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
        selections = []

        for part in photoset.parts:
            selection = self.__selector.select(part)

            selections += selection

        if selections:
            represent = ", ".join(selections)

            return [f"Failed {self.__name} for {represent}."]
        else:
            return []

    def ask_for_extract(self):
        if self.__hook is None:
            return False

        return util.ask_for_permission(self.__message)

    def extract(self, photoset: Photoset) -> Iterable[Problem]:
        if self.hookable:
            return self.__hook.forward(photoset)

        return []

    def rollback(self, photoset: Photoset) -> Iterable[Problem]:
        if self.hookable:
            return self.__hook.backwards(photoset)

        return []

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
        return first(inner_check.get_problems(photoset) for inner_check in self.__inner) or []


class DestinationsAwareCheck(Check):
    @abstractmethod
    def check_post_metafile(self, folder: Folder) -> Iterable[Problem]:
        pass

    @abstractmethod
    def check_group_metafile(self, folder: Folder) -> Iterable[Problem]:
        pass

    @abstractmethod
    def check_person_metafile(self, folder: Folder) -> Iterable[Problem]:
        pass

    def get_problems(self, photoset: Photoset) -> Iterable[Problem]:
        problems = []

        if photoset.justin is not None:
            problems += self.check_group_metafile(photoset.justin)

            for name_folder in photoset.justin.subfolders:
                for post_folder in folder_tree_parts(name_folder):
                    problems += self.check_post_metafile(post_folder)

        if photoset.timelapse:
            problems += self.check_post_metafile(photoset.timelapse)

        def check_event(event_folder: Folder) -> Iterable[Problem]:
            local_problems = self.check_group_metafile(event_folder)

            for post_folder_ in folder_tree_parts(event_folder):
                local_problems += self.check_post_metafile(post_folder_)

            return local_problems

        if photoset.closed is not None:
            for name_folder in photoset.closed.subfolders:
                problems += check_event(name_folder)

        if photoset.meeting is not None:
            problems += check_event(photoset.meeting)

        if photoset.my_people is not None:
            problems += self.check_post_metafile(photoset.my_people)

            for person_folder in photoset.my_people.subfolders:
                problems += self.check_person_metafile(person_folder)

        return problems


class DestinationsAwareMetaCheck(MetaCheck, DestinationsAwareCheck, ABC):
    pass
