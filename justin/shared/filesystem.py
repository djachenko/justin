import platform
import shutil
import webbrowser
from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from typing import List, Optional, Dict, Callable

from justin_utils.data import DataSize
from justin_utils.multiplexer import Multiplexable
from justin_utils.time_formatter import format_time
from justin_utils.transfer import TransferSpeedMeter, TransferTimeEstimator


# region helpers


def __subfolders(path: Path) -> List[Path]:
    if path.exists():
        return [i for i in path.iterdir() if i.is_dir()]

    return []


def __subfiles(path: Path) -> List[Path]:
    return [i for i in path.iterdir() if i.is_file()]


def __tree_is_empty(path: Path):
    return len(__subfiles(path)) == 0 and all([__tree_is_empty(subfolder) for subfolder in __subfolders(path)])


def __flatten(path: Path) -> List[Path]:
    files = []

    for entry in path.iterdir():
        if entry.is_file():
            files.append(entry)
        elif entry.is_dir():
            files += __flatten(entry)

    return files


def __check_paths(src_path: Path, dst_path: Path):
    assert isinstance(src_path, Path)
    assert isinstance(dst_path, Path)

    if dst_path == src_path.parent:
        return

    assert src_path.exists()


def open_file_manager(path: Path):
    # noinspection PyTypeChecker
    webbrowser.open(path)


# endregion

# region determining drives

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


# endregion

# region generic operations

def __handle_tree(src_path: Path, dst_path: Path, file_handler: Callable[[Path, Path], None], action_name: str):
    assert src_path.is_dir()

    dst_path = dst_path.resolve()

    files = __flatten(src_path)

    total_size = DataSize.from_bytes(sum(file.stat().st_size for file in files))
    total_copied = DataSize.from_bytes(0)

    speed_meter = TransferSpeedMeter()

    print(f"{action_name} {src_path.name} from {src_path.parent} to {dst_path}...")

    speed_meter.start()

    for index, file in enumerate(files):
        assert file.is_file()

        relative_path = file.relative_to(src_path)
        file_size = file.stat().st_size

        speed_meter.feed(file_size)

        current_speed = speed_meter.current_value

        log_string = f"{action_name} {relative_path} ({index}/{len(files)})" \
                     f" ({total_copied} / {total_size}) {current_speed}."

        estimated_time = TransferTimeEstimator.estimate(current_speed, total_size - total_copied)

        if estimated_time is not None:
            log_string += f" {format_time(estimated_time)} remaining."

        print(log_string, flush=True)

        file_handler(file, dst_path / relative_path)

        total_copied.add_bytes(file_size)

    assert __tree_is_empty(src_path)

    __remove_tree(src_path)

    print(f"Processed {len(files)}/{len(files)} files, {total_copied} / {total_size}, {speed_meter.average_value}")

    print("Finished")


# endregion

# region move operations

def __move_file(file_path: Path, new_path: Path):
    assert __get_mount(file_path) != __get_mount(new_path)

    def __move():
        __copy_file(file_path, new_path)
        __remove_file(file_path)

    try:
        __move()
    except KeyboardInterrupt:
        __move()

        raise


__move_tree = partial(__handle_tree, file_handler=__move_file, action_name="Moving")


def move(src_path: Path, dst_path: Path):
    __check_paths(src_path, dst_path)

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


# endregion

# region copy operations

def __copy_file(file_path: Path, new_path: Path):
    new_path = new_path.resolve()

    assert not new_path.exists()

    new_path.parent.mkdir(parents=True, exist_ok=True)

    assert new_path.parent.exists()
    assert new_path.parent.is_dir()

    # noinspection PyTypeChecker
    shutil.copy2(file_path, new_path)


__copy_tree = partial(__handle_tree, file_handler=__copy_file, action_name="Copying")


def copy(src_path: Path, dst_path: Path):
    __check_paths(src_path, dst_path)

    new_item_path = dst_path / src_path.name

    if src_path.is_file():
        __copy_file(src_path, new_item_path)
    elif src_path.is_dir():
        __copy_tree(src_path, new_item_path)
    else:
        assert False


# endregion

# region remove operations

def __remove_file(file_path: Path):
    file_path.unlink()


def __remove_tree(path: Path) -> None:
    assert isinstance(path, Path)
    assert path.is_dir()

    for entry in path.iterdir():
        __remove_tree(entry)

    path.rmdir()


# endregion


class Movable(ABC):
    @abstractmethod
    def move(self, path: Path):
        pass

    @abstractmethod
    def move_down(self, subfolder: str) -> None:
        pass

    @abstractmethod
    def move_up(self) -> None:
        pass

    @abstractmethod
    def copy(self, path: Path) -> None:
        pass


class PathBased(Movable):
    def __init__(self, path: Path) -> None:
        super().__init__()

        self.__path = path

    @property
    def path(self) -> Path:
        return self.__path

    def move(self, path: Path) -> None:
        # files and folders are copied differently. Also having same drive matters
        move(self.path, path)

        self.__path = path / self.path.name

    def copy(self, path: Path) -> None:
        copy(self.path, path)

    def move_down(self, subfolder: str) -> None:
        self.move(self.path.parent / subfolder)

    def move_up(self) -> None:
        self.move(self.path.parent.parent)


class File(PathBased):

    @property
    def name(self):
        return self.path.name

    @property
    def size(self):
        return self.path.stat().st_size

    def is_file(self) -> bool:
        return self.path.is_file()

    def is_dir(self) -> bool:
        return self.path.is_dir()

    @property
    def mtime(self):
        return self.path.stat().st_mtime

    def stem(self) -> str:
        name = self.path.stem

        # todo: extract this from File
        if "-" in name:
            name_and_modifier = name.rsplit("-", 1)

            modifier = name_and_modifier[1]

            if modifier.isdecimal():
                name = name_and_modifier[0]

        return name

    @property
    def extension(self) -> str:
        return self.path.suffix

    def __str__(self) -> str:
        return "File {name}".format(name=self.name)

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, File):
            return False

        return o.path == self.path


class FolderTree(PathBased, Multiplexable):
    # noinspection PyTypeChecker
    def __init__(self, path: Path) -> None:
        super().__init__(path)

        self.__backing_subtrees: Dict[str, FolderTree] = None
        self.__files: List[File] = None

    @property
    def __subtrees(self) -> Dict[str, 'FolderTree']:
        if self.__backing_subtrees is None:
            self.refresh()

        return self.__backing_subtrees

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def files(self) -> List[File]:
        if self.__files is None:
            self.refresh()

        return self.__files

    @property
    def subtrees(self) -> List['FolderTree']:
        return list(self.__subtrees.values())

    def __getitem__(self, key: str) -> Optional['FolderTree']:
        return self.__subtrees.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self.subtrees

    def flatten(self) -> List[File]:
        result = self.files.copy()

        for subtree in self.subtrees:
            result += subtree.flatten()

        return result

    def file_count(self) -> int:
        return sum(subtree.file_count() for subtree in self.subtrees) + len(self.files)

    def empty(self) -> bool:
        return self.file_count() == 0

    def remove(self):
        assert len(self.files) == 0

        for subtree in self.subtrees:
            subtree.remove()

        self.path.rmdir()

    def refresh(self):
        self.__backing_subtrees = {}
        self.__files = []

        for child in self.path.iterdir():
            if child.is_dir():
                child_tree = FolderTree(child)

                if not child_tree.empty():
                    self.__subtrees[child.name] = child_tree
                else:
                    child_tree.remove()

            elif child.is_file():
                if child.name.lower() == ".DS_store".lower():
                    child.unlink()
                else:
                    self.files.append(File(child))

            else:
                print("Path is neither file nor dir")

                exit(1)

    def move(self, path: Path):
        super().move(path)

        self.refresh()


class TreeBased(PathBased):
    def __init__(self, tree: FolderTree) -> None:
        super().__init__(tree.path)

        self.__tree = tree

    @property
    def tree(self) -> FolderTree:
        return self.__tree

    @property
    def name(self) -> str:
        return self.tree.name

    @property
    def path(self) -> Path:
        return self.tree.path


def parse_paths(paths: List[Path]) -> List[PathBased]:
    result = []

    for path in paths:
        if path.is_file():
            result.append(File(path))
        elif path.is_dir():
            result.append(FolderTree(path))
        else:
            assert False

    return result


class RelativeFileset(Movable):

    def __init__(self, root: Path, files: List[PathBased]) -> None:
        super().__init__()

        self.__root = root
        self.__files = files

    def move(self, path: Path) -> None:
        for file in self.__files:
            absolute_path = file.path.parent

            relative_path = absolute_path.relative_to(self.__root)

            new_path = path / relative_path

            file.move(new_path)

        self.__root = path

    def move_down(self, subfolder: str) -> None:
        self.move(self.__root / subfolder)

    def move_up(self) -> None:
        self.move(self.__root.parent)

    def copy(self, path: Path) -> None:
        for file in self.__files:
            file_parent_path = file.path.parent
            file_relative_path = file_parent_path.relative_to(self.__root)

            new_path = path / file_relative_path

            file.copy(new_path)
