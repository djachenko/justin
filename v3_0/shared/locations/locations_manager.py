import os
import platform
from pathlib import Path
from typing import List

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
        return os.access(path, os.F_OK) and path.exists()

    def main_location(self) -> Path:
        return self.__locations.main() / LocationsManager.__PHOTOS_FOLDER

    def get_locations(self) -> List[Path]:
        return [location for location in self.__get_all_possible_locations() if self.__validate_location(location)]
