import platform
import shutil
import sys
from pathlib import Path
from typing import List

SEPARATOR = "/"


# noinspection PyUnusedLocal
def __copy_canceller(src, dst):
    sys.exit("Tried to copy {file_name}, aborting".format(file_name=src))


def __get_unix_mount(path: Path) -> Path:
    while True:
        if path.is_mount():
            return path

        path /= ".."


def __get_windows_mount(path: Path) -> Path:
    path = path.absolute()

    return path.parents[-1]


def __get_mount(path: Path) -> Path:
    system_name = platform.system()

    if system_name == "Darwin":
        return __get_unix_mount(path)
    elif system_name == "Windows":
        return __get_windows_mount(path)
    else:
        assert False


def __flatten(path: Path) -> List[Path]:
    files = []

    for entry in path.iterdir():
        if entry.is_file():
            files.append(entry)
        elif entry.is_dir():
            files += __flatten(entry)

    return files


def __copy_tree(src_path: Path, dst_path: Path):
    files = __flatten(src_path)

    total_size = sum(file.stat().st_size for file in files)
    total_copied = 0

    for index, file in enumerate(files):
        relative_path = file.relative_to(src_path)

        log_string = f"Copying {relative_path} ({index}/{len(files)}) ({total_copied}/{total_size})"

        print(log_string, end="")

        new_path = dst_path / relative_path

        assert not new_path.exists()
        assert new_path.parent.is_dir()

        shutil.copy2(file, new_path)

        print("\b" * len(log_string))

    print(f"Finished. Copied {len(files)}/{len(files)} files, {total_size}/{total_size} bytes.")


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

        if __tree_is_empty(file_path):
            remove_tree(file_path)
    else:
        if __get_mount(file_path) == __get_mount(dest_path):
            shutil.move(str(file_path), str(dest_path), __copy_canceller)
        else:
            __copy_tree(file_path, dest_path)


def remove_tree(path: Path) -> None:
    assert isinstance(path, Path)

    shutil.rmtree(path)


def __subfolders(path: Path) -> List[Path]:
    if path.exists():
        return [i for i in path.iterdir() if i.is_dir()]

    return []


def __subfiles(path: Path) -> List[Path]:
    return [i for i in path.iterdir() if i.is_file()]


def build_path__(*components):
    result = "/".join([component for component in components if component])

    while "//" in result:
        result = result.replace("//", "/")

    return result


def __tree_is_empty(path: Path):
    return len(__subfiles(path)) == 0 and all([__tree_is_empty(subfolder) for subfolder in __subfolders(path)])
