from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional

from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import is_parted


class Readonly:
    def __init__(self) -> None:
        super().__init__()

        self.__dict__['_Readonly__locked'] = True

    @contextmanager
    def unlock(self) -> None:
        self.__locked = False

        try:
            yield
        finally:
            # noinspection PyAttributeOutsideInit
            self.__locked = True

    def __setattr__(self, name: str, value: Any) -> None:
        assert (not self.__locked) or (name == '_Readonly__locked' and value is False)

        super().__setattr__(name, value)


class Structure(Readonly):
    SETS_KEY = "varied_folders"
    PARTS_KEY = "parts"
    FILES_KEY = "files"
    STANDALONE_FILE = "file"

    FLAG_KEYS = [
        SETS_KEY,
        FILES_KEY,
        PARTS_KEY,
        STANDALONE_FILE,
    ]

    def __init__(self, has_sets: bool, has_files: bool, has_parts: bool, files: List[str],
                 folders: Dict[str, 'Structure']) -> None:
        super().__init__()

        with self.unlock():
            self.folders = folders
            self.files = files
            self.has_parts = has_parts
            self.has_files = has_files
            self.has_sets = has_sets

    def __getitem__(self, key) -> Optional['Structure']:
        if self.has_sets and Structure.is_photoset_name(key):
            key = Structure.SETS_KEY

        return self.folders.get(key)

    @staticmethod
    def is_photoset_name(key: str) -> bool:
        components = key.split(".")

        if len(components) != 4:
            return False

        for date_component in components[:3]:
            if len(date_component) != 2 and not date_component.isdecimal():
                return False

        name_component = components[3]

        if not name_component.islower():
            return False

        name_parts = name_component.split("_")

        for name_part in name_parts:
            if not name_part.isalnum():
                return False

        return True


def validate(folder: FolderTree, structure: Structure) -> bool:
    if is_parted(folder) and structure.has_parts:
        return all(validate(subtree, structure) for subtree in folder.subtrees)

    if structure.has_sets:
        for subtree in folder.subtrees:
            if not Structure.is_photoset_name(subtree.name):
                return False

            if not validate(subtree, structure[Structure.SETS_KEY]):
                return False

    else:
        for subtree in folder.subtrees:
            if not validate(subtree, structure[subtree.name]):
                return False

    for file in folder.files:
        if file not in structure.files:
            return False

    return True


def parse_structure(description: dict, path: Path = None) -> Structure:
    if path is None:
        path = Path()

    substructures = {}
    files = [name for name, desc in description.items() if desc == Structure.STANDALONE_FILE]

    for subname, subdesc in description.items():
        if subname in Structure.FLAG_KEYS:
            continue

        substructures[subname] = parse_structure(subdesc, path / subname)

    has_implicit_sets = Structure.SETS_KEY in description
    has_files = Structure.FILES_KEY in description
    has_parts = Structure.PARTS_KEY in description

    assert not (has_implicit_sets and (has_parts or has_files))
    # assert has_files != (len(files) == 0)

    if has_implicit_sets:
        assert len(description) == 1
        assert not any(i != Structure.SETS_KEY for i in description)

        substructures = description

    return Structure(
        has_sets=has_implicit_sets,
        has_files=has_files,
        has_parts=has_parts,
        files=files,
        folders=substructures
    )
