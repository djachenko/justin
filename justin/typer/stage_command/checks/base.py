from dataclasses import dataclass
from typing import List

from justin.typer.stage_command.problems.problem import Problem


@dataclass
class StageCheckError(Exception):
    problems: List[Problem]

    def __str__(self) -> str:
        return "\n".join(str(p) for p in self.problems)
