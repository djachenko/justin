from typing import List

from filesystem.file import File
from filesystem.filesystem import Filesystem
from filesystem.path import Path
from logic.photoset.checks.base_check import BaseCheck
from logic.photoset.filters.filter import Filter
from logic.photoset.selectors.base_selector import BaseSelector
from models.photoset import Photoset


class BaseFilter(Filter):
    def __init__(self, selector: BaseSelector, filter_folder: str, prechecks: List[BaseCheck]=None) -> None:
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
            if file is None:
                a = 7

            file.move(filter_path)

    def backwards(self, photoset: Photoset) -> None:
        filter_path = self.__filter_folder_path(photoset)

        if not filter_path.exists():
            return

        filtered = Filesystem.folder(filter_path)

        for folder in filtered.subfiles():
            folder.move(self.__source_folder_path(photoset))

        for folder in filtered.subfolders():
            folder.move(self.__source_folder_path(photoset))

        File.remove(filter_path)

    def __filter_folder_path(self, photoset: Photoset) -> Path:
        return photoset.path.append_component(self.__filter_folder)

    def __source_folder_path(self, photoset: Photoset) -> Path:
        return photoset.path.append_component(self.__selector.source_folder(photoset))
