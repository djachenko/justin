from pathlib import Path
from typing import List

from v3_0.actions.archive.archive import Archive
from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.locations.locations_manager import LocationsManager
from v3_0.shared.new_structure import Structure


# todo: class is currently unused, review
class World:
    def __init__(self, disk_structure: Structure) -> None:
        super().__init__()

        self.__locations_manager = LocationsManager.instance()
        self.__archive = Archive(SingleFolderTree(self.__locations_manager.main_location()), disk_structure)

    @property
    def archive(self) -> Archive:
        return self.__archive

    @property
    def current_location(self) -> Path:
        return self.__locations_manager.current_location()

    @property
    def all_locations(self) -> List[Path]:
        return self.__locations_manager.get_locations()

    def location_of_path(self, path: Path) -> Path:
        return self.__locations_manager.location_of_path(path)
