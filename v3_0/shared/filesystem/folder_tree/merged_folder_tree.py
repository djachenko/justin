# facade for multiple trees not having any relations to each other
# like split photoset
from collections import Iterable

from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree


# noinspection PyAbstractClass
class MergedFolderTree(FolderTree):
    def __init__(self, trees: Iterable[FolderTree]) -> None:
        super().__init__()

        self.trees = trees

    def __collect(self, func):
        result = []

        for tree in self.trees:
            result += func(tree)

        return result

    @property
    def files(self) -> List[File]:
        return self.__collect(lambda tree: tree.files)

    @property
    def subtree_names(self) -> List[str]:
        return self.__collect(lambda tree: tree.subtree_names)

    def __getitem__(self, key: str) -> FolderTree:
        res = self.__collect(lambda x: x[key])

        return MergedTree(res)

    def flatten(self) -> List[File]:
        return self.__collect(lambda x: x.flatten())
