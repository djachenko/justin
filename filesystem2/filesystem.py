from typing import Optional, List

from filesystem import fs
from filesystem2.absolute_path import AbsolutePath
from filesystem2.file import File
from filesystem2.folder import Folder
from filesystem2.path import Path


class Filesystem:
    @staticmethod
    def contents(path: Path) -> List[File]:
        if not fs.path_exists__(path.to_string()):
            return []

        entries = list(fs.scandir__(path.to_string()))

        files = [File(entry) for entry in entries]

        result = []

        for file in files:
            if file.is_dir():
                result.append(Folder(file.entry))
            else:
                result.append(file)

        return result

    @staticmethod
    def file(path: AbsolutePath) -> Optional[File]:
        siblings = Filesystem.contents(path.parent())

        for file in siblings:
            if file.path == path:
                return file

        return None

    @staticmethod
    def folder(path: AbsolutePath) -> Optional[Folder]:
        file = Filesystem.file(path)

        if file.is_dir():
            return file
        else:
            return None
