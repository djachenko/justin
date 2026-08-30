from abc import abstractmethod, ABC
from typing import List, Type

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.stem_selecting import StemSelecting
from justin.typer.stage_command.problems.problem import Problem
from justin.typer.stage_command.problems.stem_problem import StemProblem


class StemChecking(StemSelecting, ABC):
    @property
    @abstractmethod
    def problem_class(self) -> Type[StemProblem]:
        raise NotImplementedError

    def get_problems(self, photoset: Photoset) -> List[Problem]:
        stems = self.select_stems(photoset)

        if not stems:
            return []

        return [self.problem_class(stems)]
