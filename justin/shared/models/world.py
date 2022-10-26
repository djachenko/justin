from pathlib import Path
from typing import List

from justin.actions.named.stage.models.stage import ArchiveStage
from justin.shared.locations.locations_manager import LocationsManager


# todo: class is currently unused, review
class World:
    def __init__(self) -> None:
        super().__init__()

        self.__locations_manager = LocationsManager.instance()
        # self.__archive = None

    @property
    def archive(self) -> ArchiveStage:
        return None  # self.__archive

    @property
    def current_location(self) -> Path:
        return self.__locations_manager.current_location()

    @property
    def all_locations(self) -> List[Path]:
        return self.__locations_manager.get_locations()

    def location_of_path(self, path: Path) -> Path:
        return self.__locations_manager.location_of_path(path)
