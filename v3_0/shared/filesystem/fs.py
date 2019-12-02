import platform
import shutil
from pathlib import Path
from typing import List

from v3_0.shared.exceptions.tried_copy_error import TriedCopyError

SEPARATOR = "/"


# noinspection PyUnusedLocal
def __copy_canceller(src, dst):
    raise TriedCopyError(f"Tried to copy {src}")


def __get_unix_mount(path: Path) -> Path:
    while True:
        if path.is_mount():
            return path

        path /= ".."
        path = path.resolve()


def __get_windows_mount(path: Path) -> Path:
    path = path.absolute()

    return list(path.parents)[-1]


def __get_mount(path: Path) -> Path:
    system_name = platform.system()
    path = path.resolve().absolute()

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


def __move_file(file_path: Path, new_path: Path):
    new_path = new_path.resolve()

    assert not new_path.exists()

    new_path.parent.mkdir(parents=True, exist_ok=True)

    assert new_path.parent.exists()
    assert new_path.parent.is_dir()

    # noinspection PyTypeChecker
    shutil.copy2(file_path, new_path)
    file_path.unlink()


def __move_tree(src_path: Path, dst_path: Path):
    dst_path = dst_path.resolve()

    files = __flatten(src_path)

    total_size = sum(file.stat().st_size for file in files) / 1024.0
    total_copied = 0

    print(f"Moving {src_path.name} from {src_path.parent} to {dst_path}...")

    for index, file in enumerate(files):
        assert file.is_file()

        relative_path = file.relative_to(src_path)
        file_size = file.stat().st_size

        log_string = f"Moving {relative_path} ({index}/{len(files)}) ({total_copied:.2f}/{total_size:.2f})"

        print(log_string, flush=True)

        __move_file(file, dst_path / relative_path)

        total_copied += file_size / 1024.0

    assert __tree_is_empty(src_path)

    remove_tree(src_path)

    print(f"Copied {len(files)}/{len(files)} files, {total_copied:.2}/{total_size:.2f} bytes.")

    print("Finished")


def move(src_path: Path, dst_path: Path):
    assert isinstance(src_path, Path)
    assert isinstance(dst_path, Path)

    if dst_path == src_path.parent:
        return

    assert src_path.exists()

    new_file_path = dst_path / src_path.name

    if __get_mount(src_path) == __get_mount(dst_path):
        new_file_path.parent.mkdir(parents=True, exist_ok=True)

        src_path.rename(new_file_path)
    elif src_path.is_dir():
        __move_tree(src_path, new_file_path)
    elif src_path.is_file():
        __move_file(src_path, new_file_path)
    else:
        assert False


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
