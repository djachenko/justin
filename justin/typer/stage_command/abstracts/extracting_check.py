from abc import abstractmethod

from justin.typer.stage_command.abstracts.check import Check
from justin.typer.stage_command.abstracts.file_mover import FileMover
from justin.typer.stage_command.checks_reporter import ChecksReporter


class ExtractingCheck(FileMover, Check):
    """
    Чек с извлечением: находит проблемы и при согласии пользователя
    перемещает файлы в карантин. FileMover стоит первым в MRO —
    его fix/unfix (с prechecks) перекрывают no-op из Hook.
    """

    @property
    @abstractmethod
    def message(self) -> str:
        raise NotImplementedError

    def should_fix(self, reporter: ChecksReporter) -> bool:
        return reporter.ask_fix(self.message)
