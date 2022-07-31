from typing import Optional

from justin.shared.filesystem import FolderTree, TreeBased
from justin.shared.models.archive.destination import Destination
from justin.shared.structure import Structure
from justin_utils import util


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

            if subtree_name not in self.__structure.folders:
                continue

            destinations[subtree_name] = Destination(subtree, self.__structure[subtree_name])

        self.__destinations = destinations

    def get_destination(self, name: str) -> Optional[Destination]:
        if name not in self.__destinations and len(self.__structure.folders) > 0:
            new_destination_path = self.path / name

            new_destination_path.mkdir(exist_ok=True, parents=True)

            return Destination(FolderTree(new_destination_path), self.__structure[name])

        return self.__destinations.get(name)
