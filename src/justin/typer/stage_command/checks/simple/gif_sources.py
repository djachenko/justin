

from dataclasses import dataclass
from typing import List

from justin.typer.stage_command.problems.stem_problem import StemProblem
from justin_utils import joins, util

from justin.typer.stage_command.abstracts.simple_check import SimpleCheck
from justin.typer.stage_command.problems.problem import Problem
from justin.shared.models.photoset import Photoset


@dataclass(frozen=True)
class MissingGifSourceProblem(StemProblem):
    def __str__(self) -> str:
        return f"Sources without gif pair: {', '.join(self.stems)}"


class GifSourcesCheck(SimpleCheck):
    @property
    def name(self) -> str:
        return "gif sources check"

    def get_problems(self, photoset: Photoset) -> List[Problem]:
        if photoset.gif is None:
            return []

        gif_sources = photoset.gif.flatten()
        sources = photoset.sources

        join = joins.right(
            gif_sources,
            sources,
            lambda gif, source: gif.stem == source.stem
        )

        missing = [source.stem for gif, source in join if gif is None]

        if not missing:
            return []

        # Спрашиваем сразу здесь — специфика этого чека
        problems = [MissingGifSourceProblem(missing)]

        if util.ask_for_permission(f"\n{problems[0]}. This ok?"):
            return []

        return problems
