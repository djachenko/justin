from pathlib import Path
from typing import Iterable, List

from v3_0.helpers import util, joins
from v3_0.filesystem.file import File
from v3_0.filesystem.movable import Movable


class Source(Movable):
    def __init__(self, raw: File, metadata: File):
        super().__init__()

        self.raw = raw

        assert raw.extension != "jpg"

        self.metadata: File = None

        if metadata is not None:
            assert raw.name_without_extension() == metadata.name_without_extension()

            self.metadata = metadata
            self.mtime = metadata.mtime
        else:
            if raw.extension == "nef":
                self.mtime = -1
            else:
                self.mtime = raw.mtime

    @property
    def name(self):
        return self.raw.name_without_extension()

    def move(self, path: Path):
        self.raw.move(path)

        if self.metadata is not None:
            self.metadata.move(path)

    def move_down(self, subfolder: str) -> None:
        self.raw.move_down(subfolder)

        if self.metadata is not None:
            self.metadata.move_down(subfolder)

    def move_up(self) -> None:
        self.raw.move_up()

        if self.metadata is not None:
            self.metadata.move_up()

    def name_without_extension(self) -> str:
        return self.name

    @property
    def size(self):
        size = self.raw.size

        if self.metadata is not None:
            size += self.metadata

        return size

    def __str__(self) -> str:
        return "Source {name}".format(name=self.name)

    @staticmethod
    def from_file_sequence(seq: Iterable[File]) -> List['Source']:
        split = list(util.split_by_predicates(
            seq,
            lambda file: file.extension.lower() in ['nef', "tif", ],
            lambda file: file.extension.lower() == "xmp"
        ))

        join = joins.left(
            split[0],
            split[1],
            lambda raw, jpeg: raw.name_without_extension() == jpeg.name_without_extension()
        )

        sources = [Source(raw, meta) for raw, meta in join]

        return sources
