from abc import abstractmethod
from pathlib import Path
from typing import List

from v3_0.shared.filesystem.file import File
from v3_0.shared.filesystem.movable import Movable


class Source(Movable):
    @property
    @abstractmethod
    def mtime(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    def stem(self) -> str:
        return self.name

    def move(self, path: Path):
        for file in self.files():
            file.move(path)

    def move_down(self, subfolder: str) -> None:
        for file in self.files():
            file.move_down(subfolder)

    def move_up(self) -> None:
        for file in self.files():
            file.move_up()

    @property
    def size(self):
        return sum([f.size for f in self.files()])

    @abstractmethod
    def files(self) -> List[File]:
        pass

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.name}"
