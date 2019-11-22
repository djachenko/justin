from pathlib import Path
from typing import List

from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.new_structure import Structure
from v3_0.actions.stage.logic.base.selector import Selector


class StructureSelector(Selector):
    def __init__(self, structure: Structure) -> None:
        super().__init__()

        self.__structure = structure

    def __inner_select(self, tree: FolderTree, structure: Structure) -> List[Path]:
        result = []

        parted = PartingHelper.is_parted(tree)

        if parted and not structure.has_parts:
            result += [subtree.path for subtree in tree.subtrees]

            return result

        if not structure.has_unlimited_files:
            result += [file.path for file in tree.files]

        for subtree in tree.subtrees:
            if structure.has_substructure(subtree.name):
                if parted:
                    next_structure = structure
                else:
                    next_structure = structure[subtree.name]

                result += self.__inner_select(subtree, next_structure)

            else:
                result.append(subtree.path)

        return result

    def select(self, photoset: Photoset) -> List[str]:
        wrong_paths = self.__inner_select(photoset.tree, self.__structure)

        relative_wrong_paths = [path.relative_to(photoset.path) for path in wrong_paths]

        relative_strings = [str(path) for path in relative_wrong_paths]

        return relative_strings
