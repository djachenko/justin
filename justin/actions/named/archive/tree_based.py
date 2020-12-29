from pathlib import Path

from justin.shared.filesystem import FolderTree


class TreeBased:
    def __init__(self, tree: FolderTree) -> None:
        super().__init__()

        self.__tree = tree

    @property
    def tree(self) -> FolderTree:
        return self.__tree

    @property
    def name(self) -> str:
        return self.tree.name

    @property
    def path(self) -> Path:
        return self.tree.path
