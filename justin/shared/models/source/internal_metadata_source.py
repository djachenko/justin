from typing import List

from justin.shared.filesystem.file import File
from justin.shared.models.source.source import Source


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
