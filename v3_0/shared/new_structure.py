import re
from pathlib import Path
from typing import List

from v3_0.shared.helpers.parting_helper import PartingHelper


class Structure:
    SETS_KEY = "varied_folders"
    PARTS_KEY = "parts"
    FILES_KEY = "files"

    __FLAG_KEYS = [
        SETS_KEY,
        FILES_KEY,
        PARTS_KEY,
    ]

    STANDALONE_FILE = "file"

    __PHOTOSET_NAME_REGEXP = "\d\d\.\d\d\.\d\d\.\w+"

    def __init__(self, name: str, description: dict, path: Path, next_level_structure: dict = None) -> None:
        super().__init__()

        self.__name = name
        self.__substructures = {}
        self.__files = []
        self.__path = path

        for subname, subdesc in description.items():
            if subdesc == Structure.STANDALONE_FILE:
                self.__files.append(subname)
            elif subname in Structure.__FLAG_KEYS:
                pass
            else:
                self.__substructures[subname] = Structure(subname, subdesc, self.__path / subname)

        self.__has_implicit_sets = Structure.SETS_KEY in description
        self.__has_files = Structure.FILES_KEY in description
        self.__has_parts = Structure.PARTS_KEY in description

        self.__next_level_structure = next_level_structure

    @property
    def name(self) -> str:
        return self.__name

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def has_substructures(self) -> bool:
        return len(self.substructures) > 0

    @property
    def substructures(self) -> List['Structure']:
        return list(self.__substructures.values())

    @property
    def has_implicit_sets(self) -> bool:
        return self.__has_implicit_sets

    @property
    def has_unlimited_files(self) -> bool:
        return self.__has_files

    @property
    def has_parts(self) -> bool:
        return self.__has_parts

    def __str__(self) -> str:
        return self.__name

    def has_file(self, item: str) -> bool:
        return self.__has_files or item in self.__files

    def has_substructure(self, item: str) -> bool:
        if item in self.__substructures:
            return True
        elif self.has_parts:
            return PartingHelper.is_part_name(item)
        else:
            return False

    def has_set(self, item: str) -> bool:
        return not self.has_substructure(item) and self.has_implicit_sets

    def __getitem__(self, key) -> 'Structure':
        if key in self.__substructures:
            return self.__substructures[key]
        elif self.__has_implicit_sets and re.match(Structure.__PHOTOSET_NAME_REGEXP, key) is not None:
            return Structure(key, self.__next_level_structure, self.path / key)
        else:
            assert False
