from typing import List, Type

from justin.typer.stage_command.problems.stem_problem import StemProblem
from justin_utils import joins

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.checks.extracting.stem_extracting_check import StemExtractingCheck


class UnselectedFilesProblem(StemProblem):
    def __str__(self) -> str:
        return f"Unselected files: {', '.join(self.stems)}"


class UnselectedCheck(StemExtractingCheck):
    @property
    def problem_class(self) -> Type[StemProblem]:
        return UnselectedFilesProblem

    @property
    def folder(self) -> str:
        return "to_select"

    @property
    def message(self) -> str:
        return "You have results without selection. Extract?"

    def select_stems(self, photoset: Photoset) -> List[str]:
        selection = photoset.not_signed.files
        results = photoset.results

        join = joins.left(
            results,
            selection,
            lambda x, y: x.stem == y.stem
        )

        return [i[0].stem for i in join if i[1] is None]