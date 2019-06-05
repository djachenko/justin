from typing import List

from v3_0 import structure
from v3_0.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.logic.base.selector import Selector
from v3_0.filesystem.movable import Movable
from v3_0.models.photoset import Photoset
from v3_0.structure import Structure


class UnnecessaryFoldersSelector(Selector):
    def __init__(self, depth=-1) -> None:
        super().__init__()

        self.__depth = depth

    def select(self, photoset: Photoset) -> List[Movable]:
        possible_destinations = structure.photoset_structure

        result = self.__descend(photoset.tree, possible_destinations, self.__depth)

        return result

    def __descend(self, entry: FolderTree, struct: Structure, depth: int) -> List[Movable]:
        if depth == 0:
            return []

        subfolders = entry.subtrees

        result = []

        for subfolder in subfolders:
            if struct.has_substructure(subfolder.name):
                result += self.__descend(subfolder, struct[subfolder.name], depth - 1)
            else:
                result.append(subfolder)

        if not struct.has_unlimited_files:
            result += entry.files

        return result
