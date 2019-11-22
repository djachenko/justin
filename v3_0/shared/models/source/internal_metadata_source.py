from typing import List

from v3_0.shared.filesystem.file import File
from v3_0.shared.models.source.source import Source


class InternalMetadataSource(Source):
    def __init__(self, jpeg: File):
        super().__init__()

        self.__jpeg = jpeg

    @property
    def mtime(self):
        return self.__jpeg.mtime

    @property
    def name(self):
        return self.__jpeg.stem()

    def files(self) -> List[File]:
        return [self.__jpeg]
