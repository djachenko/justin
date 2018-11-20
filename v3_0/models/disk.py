from typing import Iterable, Optional

import structure
from v3_0.filesystem.folder_tree.folder_tree import FolderTree
from structure import Structure
from v3_0.models.photoset import Photoset


class Disk:
    def __init__(self, root: FolderTree) -> None:
        super().__init__()

        self.root = root

    @property
    def sets(self) -> Iterable[Photoset]:
        shared_structure = structure.disk_structure

        result = Disk.__collect(self.root, shared_structure)

        return result

    def __getitem__(self, key: str) -> Optional[Photoset]:
        for photoset in self.sets:
            if photoset.name == key:
                return photoset

        return None

    @staticmethod
    def __collect(folder_root: FolderTree, structure_root: Structure) -> Iterable[Photoset]:
        result = []

        for i in structure_root.substructures:
            result += Disk.__collect(folder_root[i.name], i)

        if structure_root.has_implicit_sets:
            photosets = [Photoset(subtree) for subtree in folder_root.subtrees]

            result += photosets

        return result
