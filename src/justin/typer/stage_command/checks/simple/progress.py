

from dataclasses import dataclass
from typing import List

from justin_utils import joins

from justin.typer.stage_command.abstracts.simple_check import SimpleCheck
from justin.typer.stage_command.problems.problem import Problem
from justin.shared.models.photoset import Photoset


@dataclass(frozen=True)
class ProgressResultsProblem(Problem):
    sources: List[str]

    def __str__(self) -> str:
        return f"Sources without results in progress: {', '.join(self.sources)}"


class ProgressResultsCheck(SimpleCheck):
    @property
    def name(self) -> str:
        return "progress results check"

    def get_problems(self, photoset: Photoset) -> List[Problem]:
        if photoset.name != "progress":
            return []

        results = photoset.results
        sources = photoset.sources

        join = joins.left(sources, results, lambda s, r: s.stem == r.stem)

        missing = [s.name for s, r in join if r is None]

        if not missing:
            return []

        return [ProgressResultsProblem(missing)]


