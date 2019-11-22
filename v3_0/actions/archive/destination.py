from typing import Optional

from v3_0.actions.archive.tree_based import TreeBased
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.new_structure import Structure


class Destination(TreeBased):
    def __init__(self, tree: FolderTree, structure: Structure) -> None:
        super().__init__(tree)

        if structure.has_substructures:
            assert len(set(subtree.name for subtree in tree.subtrees)) == len(tree.subtrees)

            self.__categories = {subtree.name: subtree for subtree in tree.subtrees}
        else:
            self.__categories = None

    @property
    def has_categories(self):
        return self.__categories is not None

    def get_category(self, name: str) -> Optional[FolderTree]:
        return self.__categories.get(name)
