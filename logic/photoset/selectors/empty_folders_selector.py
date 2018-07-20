from typing import List

from filesystem.folder import Folder
from logic.photoset.selectors.base_selector import BaseSelector
from models.movable import Movable
from models.photoset import Photoset


class EmptyFoldersSelector(BaseSelector):
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
