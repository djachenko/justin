from collections import defaultdict
from pathlib import Path

from justin.shared.filesystem import Folder


def main():
    root = Folder.from_path(Path("/Users/justin/photos/stages/stage1.filter/25.05.14.embrace_tradition"))

    groups = defaultdict(lambda: [])

    keys = [
        "lavrentjeva",
        "morskoj",
        "other",
    ]

    for subfolder in root.subfolders:
        _, name = subfolder.name.split(".", maxsplit=1)

        for key in keys:
            dst = groups[key]

            if key in name:
                break

        dst.append(subfolder)

    groups = [
        groups["other"],
        groups["lavrentjeva"],
        groups["morskoj"],
    ]

    for i, group in enumerate(groups):
        for j, subfolder in enumerate(group):
            subfolder: Folder
            _, name, *_ = subfolder.name.split(".")

            index = i * 10 + j

            new_name = f"{index:02}.{name}"
            new_path = subfolder.path.with_name(new_name)

            subfolder.path.rename(new_path)


if __name__ == '__main__':
    main()
