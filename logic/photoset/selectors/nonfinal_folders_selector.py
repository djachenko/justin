from typing import List

from v3_0 import structure
from v3_0.logic.base.selector import Selector
from v3_0.filesystem.movable import Movable
from v3_0.models.photoset import Photoset


class NonfinalFoldersSelector(Selector):
    def select(self, photoset: Photoset) -> List[Movable]:
        struct = structure.photoset_structure

        supposed_folders = struct.substructures
        supposed_folders_names = [folder.name for folder in supposed_folders]

        subfolders = photoset.entry.subfolders()

        nonfinal_subfolders = [subfolder for subfolder in subfolders if subfolder.name not in supposed_folders_names]

        return nonfinal_subfolders

    def source_folder(self, photoset: Photoset) -> str:
        return ""
