from typing import List

from v3_0.filesystem.file import File
from v3_0.models.source import Source


class JpegSource(Source):
    def __init__(self, jpeg: File):
        super().__init__()

        assert jpeg.extension != "jpg"

        self.__jpeg = jpeg

    @property
    def mtime(self):
        return self.__jpeg.mtime

    @property
    def name(self):
        return self.__jpeg.name_without_extension()

    def files(self) -> List[File]:
        return [self.__jpeg]

    def __str__(self) -> str:
        return "JpegSource: {name}".format(name=self.name)
