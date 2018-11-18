import os
import shutil
import string
from pathlib import Path
from typing import List

import sys

SEPARATOR = "/"


def __isdir(path: str) -> bool:
    return os.path.isdir(path)


def __isfile(path: str) -> bool:
    return os.path.isfile(path)


def __copy_canceller(src, dst):
    sys.exit("Tried to copy {file_name}, aborting".format(file_name=src))


def move(file_path: Path, dest_path: Path):
    assert isinstance(file_path, Path)
    assert isinstance(dest_path, Path)

    if dest_path == file_path.parent:
        return

    assert file_path.exists()

    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)

    assert dest_path.is_dir()

    new_file_path = dest_path / file_path.name

    if new_file_path.exists():
        assert new_file_path.is_dir()
        assert file_path.is_dir()

        for item in file_path.iterdir():
            move(item, new_file_path)

        if tree_is_empty(file_path):
            remove_tree(file_path)
    else:
        shutil.move(str(file_path), str(dest_path), __copy_canceller)


def remove_tree(path: Path) -> None:
    assert isinstance(path, Path)

    shutil.rmtree(str(path))


def scandir__(path: str) -> List[os.DirEntry]:
    assert isinstance(path, str)

    path = path.strip("/")

    if path.endswith(":"):
        path += "/"

    return os.scandir(path)


def __disk_path(disk_letter: str) -> str:
    return disk_letter + ":"


def find_disks() -> List[str]:
    disk_letters = [__disk_path(disk_letter) for disk_letter in string.ascii_uppercase if
                    path_exists__(__disk_path(disk_letter))]

    return disk_letters


def path_exists__(path: str) -> bool:
    return os.path.exists(path)


def subfolders__(path: Path) -> List[Path]:
    if path.exists():
        return [i for i in path.iterdir() if i.is_dir()]

    return []


def subfiles__(path: Path) -> List[Path]:
    return [i for i in path.iterdir() if i.is_file()]


def build_path__(*components):
    result = "/".join([component for component in components if component])

    while "//" in result:
        result = result.replace("//", "/")

    return result


def tree_is_empty(path: Path):
    return len(subfiles__(path)) == 0 and all([tree_is_empty(subfolder) for subfolder in subfolders__(path)])
