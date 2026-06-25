from functools import cached_property

from justin.typer.stage_command.abstracts.hook import Hook
from justin.typer.stage_command.hooks.candidates import CandidatesHook
from justin.typer.stage_command.hooks.progress import ProgressHook


class HooksFactory:
    @cached_property
    def progress(self) -> Hook:
        return ProgressHook()

    @cached_property
    def candidates(self) -> Hook:
        return CandidatesHook()
