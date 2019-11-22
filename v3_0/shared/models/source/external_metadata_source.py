from typing import List

from v3_0.shared.filesystem.file import File
from v3_0.shared.models.source.source import Source


class ExternalMetadataSource(Source):
    def __init__(self, raw: File, metadata: File):
        super().__init__()

        assert raw.extension != ".jpg"

        if metadata is not None:
            assert raw.stem() == metadata.stem()

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
        return self.raw.stem()

    def files(self) -> List[File]:
        files = [self.raw]

        if self.metadata is not None:
            files.append(self.metadata)

        return files
