from typing import Iterable, List

from v3_0 import structure
from v3_0.structure import Structure
from v3_0.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.models.photoset import Photoset


class Disk:
    def __init__(self, root: FolderTree) -> None:
        super().__init__()

        self.root = root

    @property
    def sets(self) -> Iterable[Photoset]:
        shared_structure = structure.disk_structure

        result = Disk.__collect_photosets(self.root, shared_structure)

        return result

    def __getitem__(self, key: str) -> List[Photoset]:
        return [s for s in self.sets if s.name == key]

    @staticmethod
    def __collect_photosets(folder_root: FolderTree, structure_root: Structure) -> Iterable[Photoset]:
        result = []

        if folder_root is None:
            return result

        for i in structure_root.substructures:
            result += Disk.__collect_photosets(folder_root[i.name], i)

        if structure_root.has_implicit_sets:
            photosets = [Photoset(subtree) for subtree in folder_root.subtrees]

            result += photosets

        return result