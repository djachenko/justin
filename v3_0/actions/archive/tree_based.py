from pathlib import Path

from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree


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
