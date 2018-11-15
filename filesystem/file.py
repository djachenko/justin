from pathlib import Path

from filesystem import fs
from models.movable import Movable


class File(Movable):
    def __init__(self, path: Path) -> None:
        super().__init__()

        self.path = path

    @property
    def name(self):
        return self.path.name

    def is_file(self) -> bool:
        return self.path.is_file()

    def is_dir(self) -> bool:
        return self.path.is_dir()

    def move(self, path: Path):
        fs.move(self.path, path)

        self.path = path

    def move_down(self, subfolder: str) -> None:
        self.move(self.path.parent / subfolder)

    def move_up(self) -> None:
        self.move(self.path.parent.parent)

    @staticmethod
    def remove(path: Path):
        fs.remove_tree(path)

    def name_without_extension(self) -> str:
        name = self.path.stem

        if "-" in name:
            name_and_modifier = name.rsplit("-", 1)

            modifier = name_and_modifier[1]

            if modifier.isdecimal():
                name = name_and_modifier[0]

        return name

    @property
    def extension(self) -> str:
        return self.path.suffix

    def __str__(self) -> str:
        return "File {name}".format(name=self.name)
