from abc import ABC

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.check import Check
from justin.typer.stage_command.checks_reporter import ChecksReporter


class SimpleCheck(Check, ABC):
    def should_fix(self, reporter: ChecksReporter) -> bool:
        return False
