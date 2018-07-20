from abc import abstractmethod
from typing import List, Iterable

from filesystem.file import File
from filesystem.folder import Folder


class FolderTree:
    @property
    @abstractmethod
    def files(self) -> List[File]:
        pass

    @property
    @abstractmethod
    def subtree_names(self) -> List[str]:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> 'FolderTree':
        pass

    @abstractmethod
    def flatten(self) -> List[File]:
        pass


class SingleFolderTree(FolderTree):
    def __init__(self, folder: Folder = None) -> None:
        super().__init__()

        self.__subtrees = {}
        self.__files = []

        if folder is not None:
            self.__subtrees = {i.name: SingleFolderTree(i) for i in folder.subfolders()}
            self.__files = folder.subfiles()

    @property
    def files(self) -> List[File]:
        return self.__files

    @property
    def subtree_names(self) -> List[str]:
        return list(self.__subtrees.keys())

    @property
    def __subtree_values(self) -> Iterable['FolderTree']:
        return self.__subtrees.values()

    def __getitem__(self, key: str) -> FolderTree:
        if key in self.__subtrees:
            return self.__subtrees[key]
        else:
            return SingleFolderTree()

    def flatten(self) -> List[File]:
        result = self.files

        for subtree in self.__subtree_values:
            result += subtree.flatten()

        return result


class MergedTree(FolderTree):
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
