

from pathlib import Path
from typing import List

from justin.typer.stage_command.abstracts.check import Check
from justin.typer.stage_command.abstracts.extracting_check import ExtractingCheck
from justin.shared import filesystem
from justin.shared.filesystem import PathBased
from justin.shared.models.photoset import Photoset
from justin.shared.structure import Structure, StructureVisitor, XorStructure, TopStructure
from justin.typer.stage_command.problems.paths_problem import PathsProblem


class UnexpectedStructureProblem(PathsProblem):
    def __str__(self) -> str:
        joined = "\n  ".join(str(p) for p in self.paths)

        return f"Unexpected structure:\n  {joined}"


class StructureCheck(ExtractingCheck):
    """
    Проверяет структуру фотосета по заданному шаблону.

    Принимает Structure — текущий внутренний тип. Когда придёт время
    переезжать на valifold, меняются только __init__ и get_problems,
    интерфейс снаружи не меняется.
    """

    def __init__(self, structure: Structure, prechecks: List[Check] = None) -> None:
        super().__init__(prechecks)

        self.__structure = structure
        self.__visitor = _ValidateStructureVisitor(structure)

    @property
    def name(self) -> str:
        return "structure check"

    @property
    def folder(self) -> str:
        return "unexpected_structures"

    @property
    def message(self) -> str:
        return "You have some unexpected structures. Extract?"

    def get_problems(self, photoset: Photoset) -> List[PathsProblem]:
        wrong_paths = self.__visitor.validate(photoset.path)

        if not wrong_paths:
            return []

        relative = [p.relative_to(photoset.path) for p in wrong_paths]

        return [UnexpectedStructureProblem(relative)]

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        wrong_paths = self.__visitor.validate(photoset.path)

        return filesystem.parse_paths(wrong_paths)


class _ValidateStructureVisitor(StructureVisitor[List[Path]]):
    """Внутренний визитор. Заменяется на valifold при переезде."""

    def __init__(self, structure: Structure) -> None:
        super().__init__()

        self.__path: Path = None
        self.__structure = structure

    def validate(self, root: Path) -> List[Path]:
        self.__path = root
        return self.visit(self.__structure)

    def visit_xor(self, structure: XorStructure) -> List[Path]:
        validation_results = [self.visit(option) for option in structure.options]
        count_validated = sum(1 for r in validation_results if not r)

        if count_validated == 1:
            return []

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
