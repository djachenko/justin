from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, ClassVar

from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import is_parted


@dataclass
class Structure:
    SETS_KEY: ClassVar[str] = "%set_name%"
    PARTS_KEY: ClassVar[str] = "parts"
    FILES_KEY: ClassVar[str] = "files"
    STANDALONE_FILE: ClassVar[str] = "file"

    FLAG_KEYS: ClassVar[List[str]] = [
        SETS_KEY,
        FILES_KEY,
        PARTS_KEY,
        STANDALONE_FILE,
    ]

    folders: Dict[str, 'Structure']
    files: List[str]
    has_parts: bool
    has_files: bool
    has_sets: bool = field(init=False)
    set_structure: Optional['Structure']

    def __post_init__(self):
        self.has_sets = self.set_structure is not None

    def __getitem__(self, key) -> Optional['Structure']:
        if self.has_sets and Structure.is_photoset_name(key):
            return self.set_structure

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

        # !!!
        set_structure = description
    else:
        set_structure = None

    return Structure(
        set_structure=set_structure,
        has_files=has_files,
        has_parts=has_parts,
        files=files,
        folders=substructures
    )
