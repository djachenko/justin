from pathlib import Path
from typing import List

from v3_0.shared.filesystem.movable import Movable
from v3_0.shared.filesystem.path_based import PathBased


class RelativeFileset(Movable):

    def __init__(self, root: Path, files: List[PathBased]) -> None:
        super().__init__()

        self.__root = root
        self.__files = files

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
