from filesystem2.folder import Folder
from filesystem2.path import Path
from filesystem2.absolute_path import AbsolutePath
from models.movable import Movable


class FileBased(Movable):
    def __init__(self, entry: Folder) -> None:
        super().__init__()

        assert isinstance(entry, Folder)

        self.__entry = entry

    @property
    def entry(self) -> Folder:
        return self.__entry

    @property
    def path(self) -> AbsolutePath:
        return self.entry.path

    @property
    def name(self):
        return self.entry.name

    def move(self, path: Path):
        self.entry.move(path)

    def move_down(self, subfolder: str) -> None:
        self.entry.move_down(subfolder)

    def move_up(self) -> None:
        self.entry.move_up()
