import os
import shutil
import string
from typing import List

import sys

SEPARATOR = "/"


def __isdir(path: str) -> bool:
    return os.path.isdir(path)


def __isfile(path: str) -> bool:
    return os.path.isfile(path)


def __copy_canceller(src, dst):
    sys.exit("Tried to copy {file_name}, aborting".format(file_name=src))


def move(file_path: str, dest_path: str):
    assert isinstance(file_path, str)
    assert isinstance(dest_path, str)

    os.makedirs(dest_path, exist_ok=True)

    file_name = file_path.rsplit(SEPARATOR, 1)[1]
    new_file_path = build_path__(dest_path, file_name)

    if path_exists__(new_file_path) and __isdir(file_path):
        for subfile in subfiles__(file_path):
            move(subfile.path, new_file_path)

        if tree_is_empty(file_path):
            remove_tree(file_path)
    else:
        shutil.move(file_path, dest_path, __copy_canceller)


def remove_tree(path: str) -> None:
    assert isinstance(path, str)

    shutil.rmtree(path)


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


def subfolders__(path: str) -> List[os.DirEntry]:
    if path_exists__(path):
        return [i for i in scandir__(path) if i.is_dir()]

    return []


def subfiles__(path: str) -> List[os.DirEntry]:
    return [i for i in scandir__(path) if i.is_file()]


def build_path__(*components):
    result = "/".join([component for component in components if component])

    while "//" in result:
        result = result.replace("//", "/")

    return result


def folder_tree__(path, depth=-1):
    result = {subfile.name: subfile for subfile in subfiles__(path)}

    if depth != 0:
        result.update({subfolder.name: folder_tree__(subfolder.path, depth - 1) for subfolder in subfolders__(path)})

    return result


def tree_is_empty(path: str):
    return len(subfiles__(path)) == 0 and all([tree_is_empty(subfolder.path) for subfolder in subfolders__(path)])
