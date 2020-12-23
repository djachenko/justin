import glob
from argparse import ArgumentParser
from pathlib import Path


def run():
    parser = ArgumentParser()

    parser.add_argument("name", type=str)
    parser.add_argument("pattern", type=str, nargs="?", default="*")

    namespace = parser.parse_args()

    new_subfolder = namespace.name

    for str_path in glob.iglob(namespace.pattern):
        path = Path(str_path)

        new_parent = path.parent / new_subfolder

        new_parent.mkdir(exist_ok=True)

        new_path = new_parent / path.name

        path.rename(new_path)
