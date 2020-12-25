import glob
from argparse import ArgumentParser, Namespace
from math import log10
from pathlib import Path
from typing import Tuple, Callable

__SEPARATOR = "."
__INDEX_START = 1


def __is_part(path: Path):
    split_result = path.name.split(__SEPARATOR)

    return len(split_result) > 0 and split_result[0].isdecimal()


def __split_part(path: Path) -> Tuple[int, str]:
    name_parts = path.name.split(__SEPARATOR, maxsplit=1)

    index = int(name_parts[0])
    name = name_parts[1] if len(name_parts) == 2 else None

    return index, name


def __to_padded_string(number: int, length: int, padding: str) -> str:
    number_len = (int(log10(number)) if number > 0 else 0) + 1

    parts = [padding] * (length - number_len) + [str(number)]

    return "".join(parts)


def __run_make(args: Namespace):
    count = args.count
    pattern: str = args.path

    for str_path in glob.iglob(pattern):
        path = Path(str_path).absolute()

        make_parts(path, count)


def make_parts(path: Path, count: int):
    existing_subfolders = [f for f in path.iterdir() if f.is_dir()]
    existing_parts = [f for f in existing_subfolders if __is_part(f)]
    existing_indices = [__split_part(part)[0] for part in existing_parts]

    for index in range(count):
        index += __INDEX_START

        if index in existing_indices:
            continue

        part_path = path / str(index)

        assert not part_path.exists()

        part_path.mkdir(parents=True)


def __run_renumber(args: Namespace):
    pattern: str = args.path

    for str_path in glob.iglob(pattern):
        path = Path(str_path).absolute()

        renumber_parts(path)


def renumber_parts(path: Path):
    existing_subfolders = [f for f in path.iterdir() if f.is_dir()]
    existing_parts = [f for f in existing_subfolders if __is_part(f)]

    parts_count = len(existing_parts)

    if parts_count < 1:
        print(f"There are no parts at {path}")

        return

    # noinspection PyTypeChecker
    parts = [__split_part(part) + (part,) for part in existing_parts]

    parts.sort(key=lambda x: x[0])

    max_index_length = int(log10(parts_count)) + 1

    tmp_parts = []

    for index, name, path in parts:
        tmp_path = path.with_name(f"tmp_{index}")

        path.rename(tmp_path)

        tmp_parts.append((index, name, tmp_path))

    parts = tmp_parts

    for index, t in enumerate(parts):
        _, name, path = t

        index += __INDEX_START

        new_name_parts = [
            __to_padded_string(index, max_index_length, "0"),
            name
        ]

        new_name_parts = [i for i in new_name_parts if i]

        new_name = __SEPARATOR.join(new_name_parts)

        new_path = path.with_name(new_name)

        path.rename(new_path)


def run():
    parser = ArgumentParser()

    adder = parser.add_subparsers()

    make_parser = adder.add_parser("make")
    renumber_parser = adder.add_parser("renumber")

    for p in [make_parser, renumber_parser]:
        p.add_argument("path", type=str, nargs="?", default=".")

    make_parser.add_argument("count", type=int)
    make_parser.set_defaults(func=__run_make)

    renumber_parser.set_defaults(func=__run_renumber)

    namespace = parser.parse_args()

    if hasattr(namespace, "func") and namespace.func and isinstance(namespace.func, Callable):
        namespace.func(namespace)
