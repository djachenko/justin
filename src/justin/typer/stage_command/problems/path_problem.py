from dataclasses import dataclass
from pathlib import Path

from justin.typer.stage_command.problems.problem import Problem


@dataclass(frozen=True)
class PathProblem(Problem):
    path: Path
