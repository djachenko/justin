from abc import abstractmethod
from typing import List

from v3_0.filesystem.file import File
from v3_0.filesystem.path_based import PathBased


class FolderTree(PathBased):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def files(self) -> List[File]:
        pass

    @property
    @abstractmethod
    def subtree_names(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def subtrees(self) -> List['FolderTree']:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> 'FolderTree':
        pass

    @abstractmethod
    def flatten(self) -> List[File]:
        pass
