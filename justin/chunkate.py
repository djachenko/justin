from pathlib import Path

from justin_utils.util import stride

path = Path("/Users/justin/photos/stages/stage1.filter/_trash")


def forward():
    step = 10

    for i, chunk in enumerate(stride(sorted(filter(lambda x: x.is_file, path.iterdir()), key=lambda x: x.name), step)):
        chunk_folder = path / str(i)

        chunk_folder.mkdir(exist_ok=True)

        for item in chunk:
            item.rename(chunk_folder / item.name)


def backwards():
    for dir_ in path.iterdir():
        for file in dir_.iterdir():
            file.rename(path / file.name)


if __name__ == '__main__':
    forward()
