from pathlib import Path
from typing import Dict, Iterable, List

from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.locations.locations_manager import LocationsManager
from v3_0.shared.models.disk import Disk
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.new_structure import Structure


# todo: class is currently unused, review
class World:
    def __init__(self, disk_structure: Structure) -> None:
        super().__init__()

        self.__locations_manager = LocationsManager.instance()
        self.__disks_map = self.__discover_disks(disk_structure)

    @property
    def disks(self) -> Iterable[Disk]:
        return self.__disks_map.values()

    @property
    def active_disk(self) -> Disk:
        return self.__disks_map[self.__locations_manager.main_location()]

    def __discover_disks(self, disk_structure: Structure) -> Dict[Path, Disk]:
        disks_mapping = {}

        for path in self.__locations_manager.get_locations():
            disk = Disk(SingleFolderTree(path), disk_structure)

            disks_mapping[path] = disk

        return disks_mapping

    def __getitem__(self, key) -> List[Photoset]:
        return self.active_disk[key]
