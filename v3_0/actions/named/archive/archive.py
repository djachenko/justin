from typing import Optional

from v3_0.actions.named.archive.destination import Destination
from v3_0.actions.named.archive.tree_based import TreeBased
from v3_0.shared.filesystem.folder_tree import FolderTree
from v3_0.shared.helpers import util
from v3_0.shared.new_structure import Structure


class Archive(TreeBased):
    def __init__(self, tree: FolderTree, structure: Structure) -> None:
        super().__init__(tree)

        self.__structure = structure
        self.__destinations = {}

        assert util.is_distinct(tree.subtrees, key=lambda t: t.name)

        self.refresh()

    def refresh(self):
        destinations = {}

        for subtree in self.tree.subtrees:
            subtree_name = subtree.name

            if not self.__structure.has_substructure(subtree_name):
                continue

            destinations[subtree_name] = Destination(subtree, self.__structure[subtree_name])

        self.__destinations = destinations

    def get_destination(self, name: str) -> Optional[Destination]:
        if name not in self.__destinations and self.__structure.has_substructure(name):
            new_destination_path = self.path / name

            new_destination_path.mkdir()

            return Destination(FolderTree(new_destination_path), self.__structure[name])

        return self.__destinations.get(name)
