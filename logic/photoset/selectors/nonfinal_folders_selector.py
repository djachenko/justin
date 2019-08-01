from typing import List

from v3_0.shared import structure
from v3_0.stage.logic.base.selector import Selector
from v3_0.shared.filesystem.movable import Movable
from v3_0.shared.models.photoset import Photoset


class NonfinalFoldersSelector(Selector):
    def select(self, photoset: Photoset) -> List[Movable]:
        struct = structure.photoset_structure

        supposed_folders = struct.substructures
        supposed_folders_names = [folder.name for folder in supposed_folders]

        subfolders = photoset.entry.subfolders()

        nonfinal_subfolders = [subfolder for subfolder in subfolders if subfolder.name not in supposed_folders_names]

        return nonfinal_subfolders
