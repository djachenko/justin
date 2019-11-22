import os
import platform
from pathlib import Path
from typing import List, Optional

from v3_0.shared.helpers.singleton import Singleton
from v3_0.shared.locations.locations import Locations, MacOSLocations, WindowsLocations


class LocationsManager(Singleton):
    __PHOTOS_FOLDER = "photos"

    @staticmethod
    def __get_locations() -> Locations:
        system_name = platform.system()

        if system_name == "Darwin":
            return MacOSLocations()
        elif system_name == "Windows":
            return WindowsLocations()
        else:
            assert False

    def __init__(self) -> None:
        super().__init__()

        self.__locations = self.__get_locations()

    def __get_all_possible_locations(self) -> List[Path]:
        return [location / LocationsManager.__PHOTOS_FOLDER for location in self.__locations.locations()]

    @staticmethod
    def __validate_location(path: Path) -> bool:
        # noinspection PyTypeChecker
        return os.access(path, os.F_OK) and path.exists()

    def main_location(self) -> Path:
        return self.__locations.main() / LocationsManager.__PHOTOS_FOLDER

    def get_locations(self) -> List[Path]:
        return [location for location in self.__get_all_possible_locations() if self.__validate_location(location)]

    def current_location(self) -> Optional[Path]:
        current_path = Path.cwd()

        return self.location_of_path(current_path)

    def location_of_path(self, path: Path) -> Optional[Path]:
        path = path.absolute()

        all_locations = self.get_locations()

        for location in all_locations:
            if location in path.parents or path in location.parents:
                return location

        return None
