from pathlib import Path
from typing import List

from justin.shared.filesystem import FolderTree
# from justin.shared.place import Place
from justin.shared.locations.locations_manager import LocationsManager
from justin.shared.models.archive.archive import Archive
from justin.shared.structure import Structure


# todo: class is currently unused, review
def get_sets_locations(struct: Structure, root_path: Path) -> List[Path]:
    if struct is None:
        return []

    if struct.has_sets:
        return [root_path]

    result = []

    for name, substructure in struct.folders.items():
        result += get_sets_locations(substructure, root_path / name)

    return result


class World:
    LOCATION_MAPPING = {
        "stages": {
            ""
        }
    }

    def __init__(self, disk_structure: Structure) -> None:
        super().__init__()

        self.__locations_manager = LocationsManager.instance()
        self.__archive = Archive(FolderTree(self.current_location), disk_structure)
        self.__structure = disk_structure

        # sets_locations = get_sets_locations(disk_structure, Path())

        # assert set(sets_locations) == World.LOCATION_MAPPING.keys()

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

    # def entity_for_path(self, path: Path) -> Place:
    #     location_of_path = self.location_of_path(path)
    #
    #     relative_path = path.relative_to(location_of_path)
    #
    #     assert relative_path in World.LOCATION_MAPPING
    #
    #     return World.LOCATION_MAPPING[relative_path]
