import os
import platform
import shutil
import string
from abc import abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import List, Iterable, Type

from justin.shared.helpers.utils import JsonSerializable, Json
from justin.shared.metafile import MetaFolder, LocationMetafile
from justin.shared.models.photoset import Photoset
from justin_utils.util import bfs, T


class Roots:
    @abstractmethod
    def get_roots(self) -> List[Path]:
        pass

    def exclude(self) -> List[Path]:
        return []


class WindowsRoots(Roots):
    @lru_cache()
    def get_roots(self) -> List[Path]:
        return [Path(disk_letter + ":/") for disk_letter in string.ascii_uppercase]


class MacOSRoots(Roots):
    @lru_cache()
    def get_roots(self) -> List[Path]:
        return [
            Path.home() / "photos",
            Path("/Volumes")
        ]

    def exclude(self) -> List[Path]:
        return [
            Path("/Volumes/Macintosh HD")
        ]


class Location(JsonSerializable):
    def __init__(self, folder: MetaFolder) -> None:
        super().__init__()

        self.__folder = folder

    @property
    @lru_cache()
    def __metafile(self) -> LocationMetafile:
        return self.__folder.get_metafile(LocationMetafile)

    @property
    def name(self) -> str:
        return self.__metafile.location_name

    @property
    def description(self) -> str:
        return self.__metafile.location_description

    @property
    def path(self) -> Path:
        return self.__folder.path

    def get_free_space(self) -> int:
        total, used, free = shutil.disk_usage(self.path)

        print("total: ", total / 2 ** 30)
        print("used: ", used / 2 ** 30)
        print("free: ", free / 2 ** 30)

        return free

    @lru_cache()
    def get_sets(self) -> Iterable[Photoset]:
        photosets = []

        def wider(folder: MetaFolder) -> List[MetaFolder]:
            if folder.name == "stages":
                return []

            if Photoset.is_photoset(folder):
                photosets.append(Photoset.from_folder(folder))

                return []
            else:
                return folder.subfolders

        bfs(self.__folder, wider)

        return photosets

    def __truediv__(self, other):
        return self.__folder / other

    @staticmethod
    def is_location(candidate: Path):
        return MetaFolder.from_path(candidate).has_metafile(LocationMetafile)

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        assert isinstance(json_object, str)

        return Location(MetaFolder.from_path(Path(json_object)))

    def as_json(self) -> Json:
        return str(self.name)


class World:
    __PHOTOS_FOLDER = "photos"

    @staticmethod
    def __get_roots() -> Roots:
        system_name = platform.system()

        if system_name == "Darwin":
            return MacOSRoots()
        elif system_name == "Windows":
            return WindowsRoots()
        else:
            assert False

    def __init__(self) -> None:
        super().__init__()

        self.__roots = self.__get_roots()

    # caching not needed, may be used for refresh
    def __discover_locations(self) -> List[Location]:
        roots = self.__roots.get_roots().copy()

        locations = []

        counter = 0

        while roots:
            if counter > 1000:
                print("Counter exceeded")
                exit(1)
            else:
                counter += 1

            try:
                candidate = roots.pop(0)

                print(candidate)

                if candidate in self.__roots.exclude():
                    continue

                if Location.is_location(candidate):
                    locations.append(Location(MetaFolder.from_path(candidate)))
                else:
                    roots += [sub for sub in candidate.iterdir() if sub.is_dir() and not sub.name.startswith(".")]
            except PermissionError:
                pass

        return locations

    @staticmethod
    def __validate_location(path: Path) -> bool:
        # noinspection PyTypeChecker
        return os.access(path, os.F_OK) and path.exists()

    @lru_cache()
    def get_locations(self) -> List[Location]:
        return self.__discover_locations()

    def current_location(self) -> Location | None:
        current_path = Path.cwd()

        return self.location_of_path(current_path)

    def location_of_path(self, path: Path) -> Location | None:
        path = path.absolute()

        all_locations = self.get_locations()

        for location in all_locations:
            if path.is_relative_to(location.path):
                return location

        return None
