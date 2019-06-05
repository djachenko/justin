from pathlib import Path
from typing import List

from v3_0.helpers import joins
from v3_0.filesystem.relative_fileset import RelativeFileset
from v3_0.logic.base.abstract_check import AbstractCheck
from v3_0.logic.base.selector import Selector
from v3_0.models.photoset import Photoset


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

    def forward(self, photoset: Photoset) -> None:
        if not all([precheck.check(photoset) for precheck in self.__prechecks]):
            return

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

        virtual_set = RelativeFileset(photoset.path, files_to_move)

        virtual_set.move_down(self.__filter_folder)

        photoset.tree.refresh()

    def backwards(self, photoset: Photoset) -> None:
        filtered = photoset.tree[self.__filter_folder]

        if not filtered:
            return

        filtered_set = RelativeFileset(filtered.path, filtered.flatten())

        filtered_set.move_up()

        photoset.tree.refresh()
