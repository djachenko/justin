from typing import List, Type

from justin.typer.stage_command.problems.stem_problem import StemProblem
from justin_utils import joins

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.checks.extracting.stem_extracting_check import StemExtractingCheck


class OddSelectionProblem(StemProblem):
    def __str__(self) -> str:
        return f"Selections without results: {', '.join(self.stems)}"


class OddSelectionCheck(StemExtractingCheck):
    @property
    def problem_class(self) -> Type[StemProblem]:
        return OddSelectionProblem

    @property
    def folder(self) -> str:
        return "odd_selection"

    @property
    def message(self) -> str:
        return "You have selections without results. Extract?"


    def select_stems(self, photoset: Photoset) -> List[str]:
        not_signed = photoset.not_signed

        if not_signed is None:
            return []

        results = photoset.results

        join = joins.left(
            not_signed.files,
            results,
            lambda x, y: x.stem == y.stem
        )

        return [i[0].stem for i in join if i[1] is None]
