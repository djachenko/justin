import os
from datetime import datetime

from filesystem import fs
from filesystem.path import Path
from models.movable import Movable


class File(Movable):
    def __init__(self, entry: os.DirEntry) -> None:
        super().__init__()

        self.__set_state(entry)

    def __set_state(self, entry):
        self.entry = entry
        self.path: Path = Path.from_string(entry.path)
        self.__name: str = entry.name

        stat = entry.stat()

        self.size = stat.st_size
        self.mtime = stat.st_mtime  #

        self.time = datetime.fromtimestamp(stat.st_mtime)

        self.__is_file = entry.is_file()
        self.__is_dir = entry.is_dir()

    @property
    def name(self):
        return self.__name

    def is_file(self) -> bool:
        return self.__is_file

    def is_dir(self) -> bool:
        return self.__is_dir

    def move(self, path: Path):
        fs.move(self.path.to_string(), path.to_string())

        new_file = File.create(path.append_component(self.name))

        self.__set_state(new_file.entry)

        # todo: UPDATE ENTRY!!!

    def move_down(self, subfolder: str) -> None:
        self.move(self.path.parent().append_component(subfolder))

    def move_up(self) -> None:
        self.move(self.path.parent().parent())

    def rename(self, new_name: str) -> None:
        if new_name == self.name:
            return

        new_path = self.path.parent().append_component(new_name)

        assert not new_path.exists()

        self.move(new_path)

    @staticmethod
    def remove(path: Path):
        fs.remove_tree(path.to_string())

    def name_without_extension(self) -> str:
        if self.is_dir() or "." not in self.name:
            return self.name
        else:
            name = self.name.rsplit(".", 1)[0]

            name_and_modifier = name.rsplit("-", 1)

            if len(name_and_modifier) > 1:
                modifier = name_and_modifier[1]

                if modifier.isdecimal():
                    name = name_and_modifier[0]

            return name

    @property
    def extension(self) -> str:
        if self.is_dir() or "." not in self.name:
            return ""
        else:
            return self.name.rsplit(".", 1)[1].lower()

    @staticmethod
    def create(path: Path) -> 'File':
        results = map(File, fs.scandir__(path.parent().to_string()))

        destined = [result for result in results if result.path == path]

        assert len(destined) == 1

        file = destined[0]

        return file

    def __str__(self) -> str:
        return "File {name}".format(name=self.name)
