from pathlib import Path
from typing import List

from v3_0.filesystem.file import File
from v3_0.filesystem.movable import Movable


class RelativeFileset(Movable):

    def __init__(self, root: Path, files: List[File]) -> None:
        super().__init__()

        self.__root = root
        self.__files = files

    def add_file(self, file: File) -> None:
        assert self.__root in file.path.parents

        self.__files.append(file)

    def move(self, path: Path) -> None:
        for file in self.__files:
            absolute_path = file.path.parent

            relative_path = absolute_path.relative_to(self.__root)

            new_path = path / relative_path

            file.move(new_path)

        self.__root = path

    def move_down(self, subfolder: str) -> None:
        self.move(self.__root / subfolder)

    def move_up(self) -> None:
        self.move(self.__root.parent)
