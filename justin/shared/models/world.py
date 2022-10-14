import platform
import string
from functools import lru_cache
from pathlib import Path
from typing import List

from justin.actions.named.stage.models.stage import Archive
from justin.shared.filesystem import Folder
from justin.shared.locations.locations_manager import LocationsManager
from justin.shared.locations.locations_new import Location
from justin.shared.metafile import LocationMetafile
from justin.shared.structure_old import OldStructure


# todo: class is currently unused, review
class World:
    def __init__(self, disk_structure: OldStructure) -> None:
        super().__init__()

        self.__locations_manager = LocationsManager.instance()
        # self.__archive = None

    @property
    def archive(self) -> Archive:
        return None  # self.__archive

    @property
    def current_location(self) -> Path:
        return self.__locations_manager.current_location()

    @property
    def all_locations(self) -> List[Path]:
        return self.__locations_manager.get_locations()

    def location_of_path(self, path: Path) -> Path:
        return self.__locations_manager.location_of_path(path)

    @lru_cache()
    def find_locations(self) -> List[Location]:
        system_name = platform.system()

        if system_name == "Darwin":
            roots = ["/"]
        elif system_name == "Windows":
            roots = [disk_letter + ":/" for disk_letter in string.ascii_uppercase]
        else:
            assert False

        root_paths = [Folder(Path(root)) for root in roots]

        queue = root_paths
        locations = []

        while queue:
            current = queue.pop(0)

            if current.has_metafile(LocationMetafile):
                metafile = current.get_metafile(LocationMetafile)

                locations.append(Location.from_folder(
                    folder=current,
                    config=Location.Config(
                        name=metafile.location_name,
                        state=metafile.location_state,
                        global_order=metafile.location_order
                    )
                ))
            else:
                queue += current.subfolders

        return locations
