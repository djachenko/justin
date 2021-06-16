import string
from abc import abstractmethod
from pathlib import Path
from typing import List


class Locations:
    @abstractmethod
    def locations(self) -> List[Path]:
        pass


class WindowsLocations(Locations):
    def locations(self) -> List[Path]:
        return [Path.home()] + [Path(disk_letter + ":/") for disk_letter in string.ascii_uppercase]


class MacOSLocations(Locations):
    def locations(self) -> List[Path]:
        return [Path.home()] + list(Path("/Volumes").iterdir())
