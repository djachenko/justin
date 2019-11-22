import string
from abc import abstractmethod
from pathlib import Path
from typing import List


class Locations:
    def locations(self) -> List[Path]:
        assert self.main() not in self.secondary_locations()

        return [self.main()] + self.secondary_locations()

    @abstractmethod
    def main(self) -> Path:
        pass

    @abstractmethod
    def secondary_locations(self) -> List[Path]:
        pass


class WindowsLocations(Locations):
    def main(self) -> Path:
        return Path("D:/")

    def secondary_locations(self) -> List[Path]:
        return [Path.home()] + \
               [Path(disk_letter + ":/") for disk_letter in string.ascii_uppercase if disk_letter != "D"]


class MacOSLocations(Locations):
    def main(self) -> Path:
        return Path.home()

    def secondary_locations(self) -> List[Path]:
        return list(Path("/Volumes").iterdir())
