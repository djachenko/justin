from typing import Iterable, List

from v3_0.filesystem.file import File
from v3_0.helpers import util, joins
from v3_0.models.source.jpeg_source import JpegSource
from v3_0.models.source.raw_source import RawSource
from v3_0.models.source.source import Source


class SourcesParser:
    @staticmethod
    def from_file_sequence(seq: Iterable[File]) -> List[Source]:
        split = list(util.split_by_predicates(
            seq,
            lambda file: file.extension.lower() in ['.nef', ".tif", ],
            lambda file: file.extension.lower() == ".xmp",
            lambda file: file.extension.lower() in ['.jpg', ".dng"]
        ))

        join = joins.left(
            split[0],
            split[1],
            lambda raw, xmp: raw.stem() == xmp.stem()
        )

        raws = [RawSource(raw, meta) for raw, meta in join]
        jpegs = [JpegSource(jpeg) for jpeg in split[2]]

        # noinspection PyTypeChecker
        sources = raws + jpegs

        return sources
