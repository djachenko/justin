from typing import List

from v3_0.shared.filesystem.path_based import PathBased
from v3_0.shared.helpers import joins
from v3_0.shared.filesystem.relative_fileset import RelativeFileset
from v3_0.actions.stage.logic.base.abstract_check import AbstractCheck
from v3_0.actions.stage.logic.base.selector import Selector
from v3_0.shared.models.photoset import Photoset


class Extractor:
    def __init__(self, selector: Selector, filter_folder: str, prechecks: List[AbstractCheck] = None) -> None:
        super().__init__()

        if not prechecks:
            prechecks = []

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

        jpegs_join = joins.left(
            selection,
            photoset.big_jpegs,
            lambda s, f: s == f.stem()
        )

        sources_join = list(joins.left(
            selection,
            photoset.sources,
            lambda s, f: s == f.stem()
        ))

        jpegs_to_move = [e[1] for e in jpegs_join]

        sources_contents_to_move = []

        for sources_pair in sources_join:
            for file in sources_pair[1].files():
                sources_contents_to_move.append(file)

        files_to_move = jpegs_to_move + sources_contents_to_move

        return files_to_move

    # todo: introduce exception
    def forward(self, photoset: Photoset) -> bool:
        if not self.__run_prechecks(photoset):
            return False

        files_to_move = self.files_to_extract(photoset)

        virtual_set = RelativeFileset(photoset.path, files_to_move)

        virtual_set.move_down(self.__filter_folder)

        photoset.tree.refresh()

        return True

    # todo: introduce exception
    def backwards(self, photoset: Photoset) -> bool:
        if not self.__run_prechecks(photoset):
            return False

        filtered = photoset.tree[self.__filter_folder]

        if not filtered:
            return True

        filtered_photoset = Photoset(filtered)

        if not self.__run_prechecks(filtered_photoset):
            return False

        filtered_set = RelativeFileset(filtered.path, filtered.flatten())

        filtered_set.move_up()

        photoset.tree.refresh()

        return True
