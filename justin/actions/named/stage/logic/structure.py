from pathlib import Path
from typing import List

from justin.actions.named.stage.logic.base import Extractor, Selector
from justin.shared import filesystem
from justin.shared.filesystem import FolderTree, PathBased
from justin.shared.helpers.parts import is_parted, folder_tree_parts
from justin.shared.models.photoset import Photoset
from justin.shared.structure import Structure


class StructureSelector(Selector):
    def __init__(self, structure: Structure) -> None:
        super().__init__()

        self.__structure = structure

    def __inner_select(self, tree: FolderTree, structure: Structure) -> List[Path]:
        result = []

        if is_parted(tree):
            if structure.has_parts:
                for part in folder_tree_parts(tree):
                    result += self.__inner_select(part, structure)
            else:
                result += [subtree.path for subtree in tree.subtrees]

            return result

        for subtree in tree.subtrees:
            if subtree.name not in structure.folders:
                result.append(subtree.path)
            else:
                result += self.__inner_select(subtree, structure[subtree.name])

        if not structure.has_files:
            result += [file.path for file in tree.files]

        return result

    def select(self, photoset: Photoset) -> List[str]:
        wrong_paths = self.__inner_select(photoset.tree, self.__structure)

        relative_wrong_paths = [path.relative_to(photoset.path) for path in wrong_paths]

        relative_strings = [str(path) for path in relative_wrong_paths]

        return relative_strings


class StructureExtractor(Extractor):
    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        relative_path_strings = self.selector.select(photoset)

        relative_paths = [Path(string) for string in relative_path_strings]

        absolute_paths = [photoset.path / path for path in relative_paths]

        return filesystem.parse_paths(absolute_paths)
