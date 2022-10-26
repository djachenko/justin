from pathlib import Path
from typing import List

from justin.actions.named.stage.logic.base import Extractor, Selector
from justin.shared import filesystem
from justin.shared.filesystem import PathBased
from justin.shared.models.photoset import Photoset
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

        wrong_paths = self.visit(self.__structure)

        relative_wrong_paths = [path.relative_to(root_path) for path in wrong_paths]

        relative_strings = [str(path) for path in relative_wrong_paths]

        return relative_strings

    # endregion Selector


class StructureExtractor(Extractor):
    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        relative_path_strings = self.selector.select(photoset)

        relative_paths = [Path(string) for string in relative_path_strings]

        absolute_paths = [photoset.path / path for path in relative_paths]

        return filesystem.parse_paths(absolute_paths)
