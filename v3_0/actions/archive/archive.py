from typing import Optional

from v3_0.actions.archive.destination import Destination
from v3_0.actions.archive.tree_based import TreeBased
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.new_structure import Structure


class Archive(TreeBased):
    def __init__(self, tree: FolderTree, structure: Structure) -> None:
        super().__init__(tree)

        assert len(set(subtree.name for subtree in tree.subtrees)) == len(tree.subtrees)

        destinations = {}

        for subtree in tree.subtrees:
            subtree_name = subtree.name

            if not structure.has_substructure(subtree_name):
                continue

            destinations[subtree_name] = Destination(subtree, structure[subtree_name])

        self.__destinations = destinations

    def get_destination(self, name: str) -> Optional[Destination]:
        return self.__destinations.get(name)
