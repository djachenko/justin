import string
from pathlib import Path
from typing import Optional, Dict, Iterable

from filesystem2.absolute_path import AbsolutePath
from v3_0.models.disk import Disk
from v3_0.models.photoset import Photoset


class World:
    __PHOTOS_FOLDER = "photos"
    __ACTIVE_DISK = "D"

    @property
    def __disks_map(self) -> Dict[str, Disk]:
        return World.__discover_disks()

    @property
    def disks(self) -> Iterable[Disk]:
        return self.__disks_map.values()

    @property
    def active_disk(self) -> Disk:
        return self.__disks_map[World.__ACTIVE_DISK]

    @staticmethod
    def __disk(disk_letter: str) -> Optional[Disk]:
        pattern = ":/" + World.__PHOTOS_FOLDER

        path_string = disk_letter + pattern
        path: AbsolutePath = AbsolutePath.from_string(path_string)

        if path.exists():
            return Disk(path)

        return None

    @staticmethod
    def __discover_disks() -> Dict[str, Disk]:
        disks_mapping = {}

        for disk_letter in string.ascii_uppercase:
            path = Path(disk_letter + ":") / "photos"

            if path.exists():
                disk = Disk()

            if disk is not None:
                disks_mapping[disk_letter] = disk

        return disks_mapping

    def __getitem__(self, key) -> Photoset:
        return self.active_disk[key]


if __name__ == '__main__':
    world = World()

    disks = world.disks
    active_disk = world.active_disk
    sets = active_disk.sets

    name = "16.08.28.utkinarium"

    photoset = world.active_disk[name]

    bases = photoset.split_bases()

    chosen_base = bases[0]

    published_path = AbsolutePath.from_string("D:/photos/stages/stage4.published")

    # photoset.split_forward(chosen_base, published_path)

    a = 7
