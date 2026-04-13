

from dataclasses import dataclass
from typing import List

from justin_utils import joins

from justin.typer.stage_command.abstracts.simple_check import SimpleCheck
from justin.typer.stage_command.problems.problem import Problem
from justin.shared.models.photoset import Photoset


@dataclass(frozen=True)
class OutdatedMetadataProblem(Problem):
    files: List[str]

    def __str__(self) -> str:
        joined = ", ".join(self.files)
        return f"Outdated metadata for: {joined}"


class MetadataCheck(SimpleCheck):
    @property
    def name(self) -> str:
        return "metadata check"

    def get_problems(self, photoset: Photoset) -> List[Problem]:
        results = photoset.big_jpegs
        sources = photoset.sources

        join = joins.inner(
            results,
            sources,
            lambda jpeg, source: jpeg.stem == source.stem
        )

        time_diffs = [
            (jpeg.name, jpeg.mtime - source.mtime)
            for jpeg, source in join
        ]

        outdated = [name for name, diff in time_diffs if diff > 0]

        if not outdated:
            return []

        return [OutdatedMetadataProblem(outdated)]
