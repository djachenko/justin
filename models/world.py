from typing import Iterable, Optional

from filesystem import fs
from filesystem.folder import Folder
from filesystem.mock_dir_entry import MockDirEntry
from filesystem.path import Path
from models.disk import Disk
from models.photoset import Photoset


class World:
    __PHOTOS_FOLDER = "photos"

    def __init__(self) -> None:
        super().__init__()

    @property
    def disks(self) -> Iterable[Disk]:
        disk_letters = [(photo_disk, Folder(MockDirEntry(photo_disk))) for photo_disk in fs.find_disks()]

        photo_disks = [(name, disk_letter) for name, disk_letter in disk_letters if
                       disk_letter.has_subfolder(World.__PHOTOS_FOLDER)]

        return [Disk(name, disk.subfolder(World.__PHOTOS_FOLDER)) for name, disk in photo_disks]

    @property
    def sets(self) -> Iterable[Photoset]:
        return []

    def element_by_path(self, path: Path) -> object:
        disk = self.disk_by_path(path)

        if disk is not None:
            return disk.element_by_path(path)
        else:
            return None

    def disk_by_path(self, path: Path) -> Optional[Disk]:
        return next(filter(lambda disk: disk.path.is_subpath(path), self.disks), None)

    def valid_path(self, path: Path) -> bool:
        return self.element_by_path(path) is not None
