from abc import abstractmethod
from pathlib import Path
from typing import List, Optional

from v3_0.shared.filesystem.file import File
from v3_0.shared.filesystem.path_based import PathBased


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
    def __getitem__(self, key: str) -> Optional['FolderTree']:
        pass

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        pass

    @abstractmethod
    def flatten(self) -> List[File]:
        pass

    @abstractmethod
    def refresh(self):
        pass

    def move(self, path: Path):
        super().move(path)

        self.refresh()

    def move_down(self, subfolder: str) -> None:
        super().move_down(subfolder)

        self.refresh()

    def move_up(self) -> None:
        super().move_up()

        self.refresh()


