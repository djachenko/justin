from dataclasses import dataclass
from pathlib import Path
from typing import List

from justin.typer.stage_command.problems.problem import Problem


@dataclass(frozen=True)
class PathsProblem(Problem):
    paths: List[Path]
