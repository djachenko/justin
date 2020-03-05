from typing import List

from v3_0.actions.named.stage.logic.base.abstract_check import AbstractCheck
from v3_0.actions.named.stage.logic.base.selector import Selector
from v3_0.actions.named.stage.logic.exceptions.extractor_error import ExtractorError
from v3_0.shared.filesystem.path_based import PathBased
from v3_0.shared.filesystem.relative_fileset import RelativeFileset
from v3_0.shared.helpers import photoset_utils
from v3_0.shared.models.photoset import Photoset


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
