import shutil
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, List

from justin.shared.filesystem import Folder
from justin.shared.metafile import PhotosetMetafile
from justin.shared.models.photoset import Photoset
from justin_utils.data import DataSize


class Location:
    __STAGES_FOLDER = "stages"

    class State(Enum):
        ACTIVE = auto()
        PASSIVE = auto()

    @dataclass(frozen=True)
    class Config:
        name: str
        state: 'Location.State'
        global_order: int

    def __init__(self, folder: Folder, config: Config) -> None:
        super().__init__()

        self.__folder = folder
        self.__name = config.name
        self.__state = config.state
        self.__order = config.global_order

    def sets(self) -> Iterable[Photoset]:
        def collect_sets(folder: Folder) -> List[Photoset]:
            if self.__state == Location.State.ACTIVE and folder.name == Location.__STAGES_FOLDER:
                return []

            if folder.has_metafile(PhotosetMetafile):
                return [Photoset.from_folder(folder)]

            result = []

            for item in folder.subfolders:
                result += collect_sets(item)

        return collect_sets(self.__folder)

    def empty_space(self) -> DataSize:
        _, _, empty_space = shutil.disk_usage(self.__folder.path)

        return DataSize.from_bytes(empty_space)

    def move_from(self, other: 'Location', folder: Folder) -> None:
        assert isinstance(other, Location)

        if other == self:
            return

        if other.empty_space() < folder.size():
            print("Not enough space.")

            return

        relative_path = folder.path.relative_to(other.__folder.path)

        new_path = self.__folder.path / relative_path

        folder.move(new_path.parent)

    @classmethod
    def from_folder(cls, folder: Folder, config: Config) -> 'Location':
        return cls(folder, config)

    def __lt__(self, other: 'Location') -> bool:
        return self.__order < other.__order
