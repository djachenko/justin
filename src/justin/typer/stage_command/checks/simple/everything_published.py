from typing import List, Type

from justin.typer.stage_command.abstracts.stem_simple_check import StemSimpleCheck
from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.problems.stem_problem import StemProblem


class UnpublishedFilesProblem(StemProblem):
    def __str__(self) -> str:
        return f"Not everything is published: {', '.join(self.stems)}"


class EverythingIsPublishedCheck(StemSimpleCheck):
    @property
    def name(self) -> str:
        return "everything is published check"

    @property
    def problem_class(self) -> Type[StemProblem]:
        return UnpublishedFilesProblem

    def select_stems(self, photoset: Photoset) -> List[str]:
        if photoset.justin is None:
            return []

        return [file.stem for file in photoset.justin.files]
