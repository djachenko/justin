from typing import List

import structure
from filesystem.folder import Folder
from logic.photoset.selectors.base_selector import BaseSelector
from models.movable import Movable
from models.photoset import Photoset
from structure import Structure


class UnnecessaryFoldersSelector(BaseSelector):
    def __init__(self, depth=-1) -> None:
        super().__init__()

        self.__depth = depth

    def source_folder(self, photoset: Photoset) -> str:
        return ""

    def select(self, photoset: Photoset) -> List[Movable]:
        possible_destinations = structure.photoset_structure

        result = self.__descend(photoset.entry, possible_destinations, self.__depth)

        return result

    def __descend(self, entry: Folder, struct: Structure, depth: int) -> List[Movable]:
        if depth == 0:
            return []

        subfolders = entry.subfolders()

        result = []

        for subfolder in subfolders:
            if struct.has_substructure(subfolder.name):
                result += self.__descend(subfolder, struct[subfolder.name], depth - 1)
            else:
                result.append(subfolder)

        if not struct.has_unlimited_files:
            result += entry.subfiles()

        return result
