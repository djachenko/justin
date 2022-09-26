from pathlib import Path
from typing import List

from justin.actions.named.stage.logic.base import Extractor, Selector
from justin.shared import filesystem
from justin.shared.filesystem import FolderTree, PathBased
from justin.shared.helpers.parts import is_parted, folder_tree_parts
from justin.shared.models.photoset import Photoset
from justin.shared.structure_old import OldStructure
from justin.shared.structure import Structure, StructureVisitor, XorStructure, TopStructure


class ValidateStructureVisitor(StructureVisitor[List[Path]], Selector):

    def __init__(self, structure: Structure) -> None:
        super().__init__()

        # noinspection PyTypeChecker
        self.__path: Path = None
        self.__structure = structure

    # region StructureVisitor

    def visit_xor(self, structure: XorStructure) -> List[Path]:
        validation_results = [self.visit(option) for option in structure.options]
        count_of_validated = len([i for i in validation_results if i])

        if count_of_validated == 1:
            return []
        else:
            return [self.__path]

    def visit_top(self, structure: TopStructure) -> List[Path]:
        assert structure is not None

        if self.__path.is_file():
            return []

        local_path = self.__path
        result = []

        for item in sorted(local_path.iterdir(), key=lambda x: x.name):
            self.__path = item

            result += self.visit(structure[item.name])

            self.__path = local_path

        return result

    def visit_none(self) -> List[Path]:
        return [self.__path]

    # endregion StructureVisitor

    # region Selector

    def select(self, photoset: Photoset) -> List[str]:

        root_path = photoset.path

        self.__path = root_path

        if isinstance(self.__structure, OldStructure):
            assert False
            wrong_paths = StructureSelector(self.__structure).inner_select(photoset.tree, self.__structure)
        else:
            wrong_paths = self.visit(self.__structure)

        relative_wrong_paths = [path.relative_to(root_path) for path in wrong_paths]

        relative_strings = [str(path) for path in relative_wrong_paths]

        return relative_strings

    # endregion Selector


class StructureSelector(Selector):
    def __init__(self, structure: OldStructure) -> None:
        super().__init__()

        self.__structure = structure

    def inner_select(self, tree: FolderTree, structure: OldStructure) -> List[Path]:
        result = []

        if is_parted(tree):
            if structure.has_parts:
                for part in folder_tree_parts(tree):
                    result += self.inner_select(part, structure)
            else:
                result += [subtree.path for subtree in tree.subtrees]

            return result

        for subtree in tree.subtrees:
            if subtree.name not in structure.folders:
                result.append(subtree.path)
            else:
                result += self.inner_select(subtree, structure[subtree.name])

        if not structure.has_files:
            result += [file.path for file in tree.files]

        return result

    def select(self, photoset: Photoset) -> List[str]:
        wrong_paths = self.inner_select(photoset.tree, self.__structure)

        relative_wrong_paths = [path.relative_to(photoset.path) for path in wrong_paths]

        relative_strings = [str(path) for path in relative_wrong_paths]

        return relative_strings


class StructureExtractor(Extractor):
    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        relative_path_strings = self.selector.select(photoset)

        relative_paths = [Path(string) for string in relative_path_strings]

        absolute_paths = [photoset.path / path for path in relative_paths]

        return filesystem.parse_paths(absolute_paths)
