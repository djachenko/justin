from pathlib import Path
from typing import List

from v3_0.helpers import joins
from v3_0.logic.check import Check
from v3_0.logic.filter import Filter
from v3_0.logic.relative_fileset import RelativeFileset
from v3_0.logic.selector import Selector
from v3_0.models.photoset import Photoset


class BaseFilter(Filter):
    def __init__(self, selector: Selector, filter_folder: str, prechecks: List[Check] = None) -> None:
        super().__init__()

        if not prechecks:
            prechecks = []

        self.__selector = selector
        self.__filter_folder = filter_folder
        self.__prechecks = prechecks

    def forward(self, photoset: Photoset) -> None:
        if not all([precheck.check(photoset) for precheck in self.__prechecks]):
            return

        selection = self.__selector.select(photoset)

        jpegs_join = joins.left(
            selection,
            photoset.big_jpegs,
            lambda s, f: s.stem() == f.stem()
        )

        sources_join = list(joins.left(
            selection,
            photoset.sources,
            lambda s, f: s.stem() == f.stem()
        ))

        jpegs_to_move = [e[1] for e in jpegs_join]

        sources_contents_to_move = []

        for sources_pair in sources_join:
            for file in sources_pair[1].files():
                sources_contents_to_move.append(file)

        files_to_move = jpegs_to_move + sources_contents_to_move

        virtual_set = RelativeFileset(photoset.path, files_to_move)

        virtual_set.move_down(self.__filter_folder)

        photoset.tree.refresh()

    def backwards(self, photoset: Photoset) -> None:
        filtered = photoset.tree[self.__filter_folder]

        if not filtered:
            return

        for file in filtered.files:
            file.move(self.__source_folder_path(photoset))

        for folder in filtered.subtrees:
            folder.move(self.__source_folder_path(photoset))

        filtered.path.rmdir()

        photoset.tree.refresh()

    def __source_folder_path(self, photoset: Photoset) -> Path:
        return photoset.path / self.__selector.source_folder(photoset)
