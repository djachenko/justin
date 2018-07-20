from typing import List, Iterable

import structure
from collect_trace import CollectTrace
from filesystem import fs
from filesystem.folder import Folder
from filesystem.folder_based import FileBased
from filesystem.mock_dir_entry import MockDirEntry
from filesystem.path import Path
from logic.disk.checks.check_structure import CheckStructure
from models.category import Category
from models.destination import Destination
from models.photoset import Photoset


class Disk(FileBased, CheckStructure):
    __disks = None

    def __init__(self, disk_letter: str, entry: Folder) -> None:
        super().__init__(entry)

        self.disk_letter = disk_letter

    @property
    def name(self):
        return self.disk_letter

    def __repr__(self) -> str:
        return self.name

    @property
    def photos_path(self):
        return self.path

    @property
    def metafile_path(self) -> Path:
        return self.photos_path.append_component(structure.METAFILE_NAME)

    @property
    def destinations(self) -> Iterable[Destination]:
        subfolders = self.entry.subfolders()

        possible_destinations = structure.disk_structure

        return [Destination(subfolder) for subfolder in subfolders
                if possible_destinations.has_substructure(subfolder.name)]

    @property
    def categories(self) -> Iterable[Category]:
        result = []

        for destination in self.destinations:
            result += destination.categories

        return result

    @property
    def photosets(self) -> Iterable[Photoset]:
        result = []

        for destination in self.destinations:
            result += destination.sets

        for category in self.categories:
            result += category.sets

        return result

    @staticmethod
    def all() -> List['Disk']:
        if Disk.__disks is None:
            disk_letters = [(photo_disk, Folder(MockDirEntry(photo_disk))) for photo_disk in fs.find_disks()]

            photo_disks = [(name, disk_letter) for name, disk_letter in disk_letters if
                           disk_letter.has_subfolder("photos")]

            Disk.__disks = [Disk(name, disk.subfolder("photos")) for name, disk in photo_disks]

        return Disk.__disks

    def __getitem__(self, key) -> Destination:
        return next(destination for destination in self.destinations if destination.name == key)

    def element_by_path(self, path: Path) -> object:
        assert self.path.is_subpath(path)

        destination = next(filter(lambda file: file.path.is_subpath(path), self.destinations), None)

        if destination is not None:
            return destination.element_by_path(path)
        else:
            return None



    def collect(self, trace: CollectTrace)->Iterable[Photoset]:
        result = []

        for destination in self.destinations:
            trace.destination = destination.name

            # result += destination.
