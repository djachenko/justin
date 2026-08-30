from abc import abstractmethod
from typing import List

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.hook import Hook
from justin.typer.stage_command.problems.problem import Problem
from justin.typer.stage_command.checks_reporter import ChecksReporter


class Check(Hook):
    @abstractmethod
    def get_problems(self, photoset: Photoset) -> List[Problem]:
        raise NotImplementedError

    @abstractmethod
    def should_fix(self, reporter: ChecksReporter) -> bool:
        raise NotImplementedError
