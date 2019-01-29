from typing import List

from filesystem.folder import Folder
from v3_0.logic.selector import Selector
from v3_0.filesystem.movable import Movable
from v3_0.models.photoset import Photoset


class EmptyFoldersSelector(Selector):
    def source_folder(self, photoset: Photoset) -> str:
        return ""

    def select(self, photoset: Photoset) -> List[Movable]:
        result = self.__descend(photoset.entry)

        return result

    def __descend(self, entry: Folder) -> List[Movable]:
        result = []

        if len(entry.all_files()) == 0:
            result.append(entry)
        else:
            for subfolder in entry.subfolders():
                result += self.__descend(subfolder)

        return result
