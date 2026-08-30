from dataclasses import dataclass
from typing import List

from justin.typer.stage_command.problems.problem import Problem


@dataclass(frozen=True)
class StemProblem(Problem):
    stems: List[str]
