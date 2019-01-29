from pathlib import Path
from typing import List

from v3_0.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.logic.check import Check
from v3_0.logic.filter import Filter
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

        filter_path = self.__filter_folder_path(photoset)

        for file in selection:
            file.move(filter_path)

        photoset.tree.refresh()

    def backwards(self, photoset: Photoset) -> None:
        filter_path = self.__filter_folder_path(photoset)

        if not filter_path.exists():
            return

        # todo: remove creation and replace with edited tree
        filtered = SingleFolderTree(filter_path)

        for file in filtered.files:
            file.move(self.__source_folder_path(photoset))

        for folder in filtered.subtrees:
            folder.move(self.__source_folder_path(photoset))

        filter_path.rmdir()

        photoset.tree.refresh()

    def __filter_folder_path(self, photoset: Photoset) -> Path:
        return photoset.path / self.__filter_folder

    def __source_folder_path(self, photoset: Photoset) -> Path:
        return photoset.path / self.__selector.source_folder(photoset)
