from typing import Iterable, List

from justin_utils import util, joins

from justin.shared.filesystem.file import File
from justin.shared.models.source.internal_metadata_source import InternalMetadataSource
from justin.shared.models.source.external_metadata_source import ExternalMetadataSource
from justin.shared.models.source.source import Source


class SourcesParser:
    @staticmethod
    def from_file_sequence(seq: Iterable[File]) -> List[Source]:
        split = list(util.split_by_predicates(
            seq,
            lambda file: file.extension.lower() in ['.nef', ".heic", ],
            lambda file: file.extension.lower() == ".xmp",
            lambda file: file.extension.lower() in ['.jpg', ".tif", ".dng"]
        ))

        join = joins.left(
            split[0],
            split[1],
            lambda raw, xmp: raw.stem() == xmp.stem()
        )

        raws = [ExternalMetadataSource(raw, meta) for raw, meta in join]
        jpegs = [InternalMetadataSource(jpeg) for jpeg in split[2]]

        # noinspection PyTypeChecker
        sources = raws + jpegs

        return sources
