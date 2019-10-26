from pathlib import Path

from v3_0.shared.filesystem import fs
from v3_0.shared.filesystem.path_based import PathBased


class File(PathBased):

    @property
    def name(self):
        return self.path.name

    @property
    def size(self):
        return self.path.stat().st_size

    def is_file(self) -> bool:
        return self.path.is_file()

    def is_dir(self) -> bool:
        return self.path.is_dir()

    @property
    def mtime(self):
        return self.path.stat().st_mtime

    @staticmethod
    def remove(path: Path):
        if path.is_dir():
            fs.remove_tree(path)
        elif path.is_file():
            path.unlink()
        else:
            assert False

    def stem(self) -> str:
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
