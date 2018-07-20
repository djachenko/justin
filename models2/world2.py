import string
from typing import List, Optional, Dict, Iterable

from filesystem2.absolute_path import AbsolutePath
from filesystem2.path import Path
from models2.disk import Disk


class World2:
    __PHOTOS_FOLDER = "photos"
    __ACTIVE_DISK = "D"

    @property
    def __disks_map(self) -> Dict[str, Disk]:
        return World2.__discover_disks()

    @property
    def disks(self) -> Iterable[Disk]:
        return self.__disks_map.values()

    @property
    def active_disk(self) -> Disk:
        return self.__disks_map[World2.__ACTIVE_DISK]

    @staticmethod
    def __disk(disk_letter: str) -> Optional[Disk]:
        pattern = ":/" + World2.__PHOTOS_FOLDER

        path_string = disk_letter + pattern
        path: AbsolutePath = AbsolutePath.from_string(path_string)

        if path.exists():
            return Disk(path)

        return None

    @staticmethod
    def __discover_disks() -> Dict[str, Disk]:
        disks_mapping = {}

        for disk_letter in string.ascii_uppercase:
            disk = World2.__disk(disk_letter)

            if disk is not None:
                disks_mapping[disk_letter] = disk

        return disks_mapping


if __name__ == '__main__':
    world = World2()

    disks = world.disks
    active_disk = world.active_disk
    sets = active_disk.sets

    name = "18.06.11.forro_na_siberia"

    photoset = world.active_disk[name]

    bases = photoset.split_bases()

    chosen_base = bases[0]

    published_path = AbsolutePath.from_string("D:/photos/stages/stage4.published")

    photoset.split_forward(chosen_base, published_path)

    a = 7
