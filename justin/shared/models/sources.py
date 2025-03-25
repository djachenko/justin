from abc import abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import List, Iterable

from justin.shared.models.exif import parse_exif, Exif
from justin_utils import util, joins

from justin.shared.filesystem import File, Movable


class Source(Movable):
    @property
    @abstractmethod
    def mtime(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def exif(self) -> Exif:
        pass

    @property
    def stem(self) -> str:
        return self.name

    def move(self, path: Path):
        for file in self.files():
            file.move(path)

    def move_down(self, subfolder: str) -> None:
        for file in self.files():
            file.move_down(subfolder)

    def move_up(self) -> None:
        for file in self.files():
            file.move_up()

    def copy(self, path: Path) -> None:
        for file in self.files():
            file.copy(path)

    @property
    def size(self):
        return sum([f.size for f in self.files()])

    @abstractmethod
    def files(self) -> List[File]:
        pass

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.name}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}: {self.name}"


class InternalMetadataSource(Source):
    TYPES = [
        ".jpg",
        ".tif",
        ".dng",
        ".heic",
    ]

    def __init__(self, jpeg: File):
        super().__init__()

        self.__jpeg = jpeg

    @property
    def mtime(self):
        return self.__jpeg.mtime

    @property
    def name(self):
        return self.__jpeg.stem

    def files(self) -> List[File]:
        return [self.__jpeg]

    @property
    @lru_cache()
    def exif(self) -> Exif:
        return parse_exif(self.__jpeg.path)


class ExternalMetadataSource(Source):
    RAW_TYPES = [
        ".nef",  # Nikon
        ".raf",  # Fujifilm GFX
        ".arw",  # Sony
    ]

    METADATA_TYPES = [
        ".xmp",
    ]

    def __init__(self, raw: File, metadata: File):
        super().__init__()

        assert raw.extension != ".jpg"

        if metadata is not None:
            assert raw.stem == metadata.stem

        self.raw = raw
        self.metadata = metadata

    @property
    def mtime(self):
        if self.metadata is not None:
            return self.metadata.mtime
        else:
            return -1

    @property
    def name(self):
        return self.raw.stem

    @property
    @lru_cache()
    def exif(self) -> Exif:
        return parse_exif(self.raw.path)

    def files(self) -> List[File]:
        files = [self.raw]

        if self.metadata is not None:
            files.append(self.metadata)

        return files


def parse_sources(seq: Iterable[File]) -> List[Source]:
    split = list(util.split_by_predicates(
        seq,
        lambda file: file.extension.lower() in ExternalMetadataSource.RAW_TYPES,
        lambda file: file.extension.lower() in ExternalMetadataSource.METADATA_TYPES,
        lambda file: file.extension.lower() in InternalMetadataSource.TYPES
    ))

    join = joins.left(
        split[0],
        split[1],
        lambda raw, xmp: raw.stem == xmp.stem
    )

    raws = [ExternalMetadataSource(raw, meta) for raw, meta in join]
    jpegs = [InternalMetadataSource(jpeg) for jpeg in split[2]]

    # noinspection PyTypeChecker
    sources = raws + jpegs

    return sources
