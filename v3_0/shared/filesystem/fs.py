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
        path = path.resolve()


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


def __move_tree(src_path: Path, dst_path: Path):
    dst_path = dst_path.resolve()
    dst_path = dst_path / src_path.name

    files = __flatten(src_path)

    total_size = sum(file.stat().st_size for file in files)
    total_copied = 0

    for index, file in enumerate(files):
        assert file.is_file()

        relative_path = file.relative_to(src_path)

        log_string = f"Moving {relative_path} ({index}/{len(files)}) ({total_copied}/{total_size})"

        print(log_string)

        new_path = dst_path / relative_path
        new_path = new_path.resolve()

        assert not new_path.exists()

        new_path.parent.mkdir(parents=True, exist_ok=True)

        assert new_path.parent.exists()
        assert new_path.parent.is_dir()

        # noinspection PyTypeChecker
        shutil.copy2(file, new_path)

        total_copied += file.stat().st_size

        file.unlink()

    assert __tree_is_empty(src_path)

    remove_tree(src_path)

    print(f"Finished. Copied {len(files)}/{len(files)} files, {total_copied}/{total_size} bytes.")


def move(src_path: Path, dst_path: Path):
    assert isinstance(src_path, Path)
    assert isinstance(dst_path, Path)

    if dst_path == src_path.parent:
        return

    assert src_path.exists()

    if not dst_path.exists():
        dst_path.mkdir(parents=True, exist_ok=True)

    assert dst_path.is_dir()

    new_file_path = dst_path / src_path.name

    if new_file_path.exists():
        assert new_file_path.is_dir()
        assert src_path.is_dir()

        for item in src_path.iterdir():
            move(item, new_file_path)

        if __tree_is_empty(src_path):
            remove_tree(src_path)
    else:
        if __get_mount(src_path) == __get_mount(dst_path):
            shutil.move(str(src_path), str(dst_path), __copy_canceller)
        else:
            __move_tree(src_path, dst_path)


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
