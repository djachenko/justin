from typing import List

import structure
from logic.photoset.selectors.base_selector import BaseSelector
from models.movable import Movable
from models.photoset import Photoset


class NonfinalFoldersSelector(BaseSelector):
    def select(self, photoset: Photoset) -> List[Movable]:
        struct = structure.photoset_structure

        supposed_folders = struct.substructures
        supposed_folders_names = [folder.name for folder in supposed_folders]

        subfolders = photoset.entry.subfolders()

        nonfinal_subfolders = [subfolder for subfolder in subfolders if subfolder.name not in supposed_folders_names]

        return nonfinal_subfolders

    def source_folder(self, photoset: Photoset) -> str:
        return ""
